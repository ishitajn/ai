from app.schemas import (
    Payload, UserProfile, MatchProfile, Location, Message, UISettings,
    UnifiedJSONOutput
)
from app.svc import (
    normalizer, embedder, index, probes, topics, planner, generator, reranker, assembler
)
import dataclasses
import json
import numpy as np

# A simple monkey-patch to make numpy arrays serializable by default
original_default = json.JSONEncoder.default
def new_default(self, obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return original_default(self, obj)
json.JSONEncoder.default = new_default


def analyze_conversation(payload: Payload) -> UnifiedJSONOutput:
    """
    The main pipeline, updated to work with the refactored services and new data schemas.
    """
    # 1. Normalize and clean text
    norm_data = normalizer.clean(payload)
    turns = norm_data.turns

    # 2. Generate embeddings for the cleaned text
    texts_to_embed = [t.text for t in turns]
    vecs = embedder.encode_cached(texts_to_embed)

    # 3. Add new embeddings to the semantic index
    if vecs.size > 0:
        index.ensure_added(turns, vecs)

    # 4. Evaluate features and probes from the conversation
    features = probes.evaluate(turns, vecs)

    # 5. Discover and categorize topics via clustering
    topics_list = topics.assign(turns, vecs)

    # 6. Perform Geo/Time planning (passing None for match data as it's not in payload)
    geo_info = planner.compute(payload.ui_settings, payload.location, None, None)

    # 7. Generate raw suggestions (ContextPack is removed for a direct call)
    raw_suggestions = generator.suggest(features, topics_list, geo_info)

    # 8. Rerank and enforce constraints on suggestions
    final_suggestions = reranker.enforce_constraints(raw_suggestions)

    # 9. Assemble the final, unified output object
    final_output = assembler.build(
        payload=payload,
        topics=topics_list,
        geo=geo_info,
        suggestions=final_suggestions,
        features=features
    )

    return final_output

if __name__ == '__main__':
    # A more complex sample payload to test the new features
    sample_payload = Payload(
        user_profile=UserProfile(user_id="u1", name="Alex"),
        match_profile=MatchProfile(match_id="m1_refactored", name="Sam"),
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

    # Run the full analysis pipeline
    result = analyze_conversation(sample_payload)

    # Convert the final dataclass to a dictionary for clean JSON printing
    result_dict = dataclasses.asdict(result)

    print("--- Unified JSON Output (Refactored) ---")
    print(json.dumps(result_dict, indent=2))
