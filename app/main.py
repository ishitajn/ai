import asyncio
import dataclasses
import json
import numpy as np

from app.schemas import (
    Payload, UserProfile, MatchProfile, Location, Message, UISettings,
    UnifiedJSONOutput
)
from app.svc import (
    normalizer, embedder, index, probes, topics, planner, generator, reranker, assembler
)

# A simple monkey-patch to make numpy arrays serializable by default
original_default = json.JSONEncoder.default
def new_default(self, obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return original_default(self, obj)
json.JSONEncoder.default = new_default


async def analyze_conversation(payload: Payload) -> UnifiedJSONOutput:
    """
    The main pipeline, refactored to be asynchronous for improved performance.
    """
    # 1. Normalize (sync)
    norm_data = normalizer.clean(payload)
    turns = norm_data.turns
    texts_to_embed = [t.text for t in turns]

    # 2. Concurrently run independent async tasks
    # We can start planning (geo) and embedding at the same time.
    geo_task = planner.compute(payload.ui_settings, payload.location, None, None)
    vecs = await embedder.encode_cached(texts_to_embed)

    # 3. Indexing (sync, stateful)
    if vecs.size > 0:
        index.ensure_added(turns, vecs)

    # 4. Concurrently run async tasks that depend on the embeddings
    # Probes and topics can be calculated at the same time.
    probes_task = probes.evaluate(turns, vecs)
    topics_task = topics.assign(turns, vecs)

    # Await all concurrent tasks to get their results
    geo_info, features, topics_list = await asyncio.gather(geo_task, probes_task, topics_task)

    # 7. Generate Suggestions (async)
    raw_suggestions = await generator.suggest(features, topics_list, geo_info)

    # 8. Rerank (sync)
    final_suggestions = reranker.enforce_constraints(raw_suggestions)

    # 9. Assemble (sync)
    final_output = assembler.build(
        payload=payload,
        topics=topics_list,
        geo=geo_info,
        suggestions=final_suggestions,
        features=features
    )

    return final_output

if __name__ == '__main__':
    sample_payload = Payload(
        user_profile=UserProfile(user_id="u1", name="Alex"),
        match_profile=MatchProfile(match_id="m1_perf_test", name="Sam"),
        location=Location(city="New York", country="USA"),
        ui_settings=UISettings(
            enhanced_nlp=True,
            local_model_config={},
            time_zone="America/New_York"
        ),
        conversation_history=[
            Message(role="user", text="Hey Sam, your profile is really interesting. I love that you're into hiking!", timestamp="2024-01-01T20:00:00Z"),
            Message(role="match", text="Hey Alex! Thanks so much. Yeah, hiking is my escape. You into the outdoors too?", timestamp="2024-01-01T20:01:00Z"),
            Message(role="user", text="Definitely! I feel like I haven't been in ages though. Work has been crazy. I'm a software dev.", timestamp="2024-01-01T20:02:00Z"),
            Message(role="match", text="Oh cool, I'm in tech too. I get the crazy work life. It makes those moments outdoors even more special. You have a very cute smile btw ;) ", timestamp="2024-01-01T20:03:00Z"),
            Message(role="user", text="Haha thanks, you're making me blush. We should totally go for a hike sometime and talk about something other than work... maybe even the ethics of AI in modern politics?", timestamp="2024-01-01T20:04:00Z")
        ]
    )

    # Run the async pipeline
    result = asyncio.run(analyze_conversation(sample_payload))

    result_dict = dataclasses.asdict(result)

    print("--- Unified JSON Output (Async Pipeline) ---")
    print(json.dumps(result_dict, indent=2))
