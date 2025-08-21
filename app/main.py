from app.schemas import (
    Payload, UserProfile, MatchProfile, Location, Message, UISettings,
    UnifiedJSONOutput, ContextPack
)
from app.svc import (
    normalizer, embedder, index, probes, topics, planner, generator, reranker, assembler
)
import dataclasses
import json
import numpy as np

# A simple monkey-patch to make numpy arrays serializable by default
# This is useful for printing the results.
original_default = json.JSONEncoder.default
def new_default(self, obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return original_default(self, obj)
json.JSONEncoder.default = new_default


def analyze_conversation(payload: Payload) -> UnifiedJSONOutput:
    """
    The main pipeline for analyzing a conversation payload, wiring all services together.
    """
    # 1. Normalize and clean text
    norm_data = normalizer.clean(payload)
    turns = norm_data.turns

    # 2. Generate embeddings for the cleaned text
    texts_to_embed = [t.text for t in turns]
    vecs = embedder.encode_cached(texts_to_embed)

    # 3. Add new embeddings to the semantic index (if any)
    if vecs.size > 0:
        index.ensure_added(turns, vecs)

    # 4. Evaluate features and probes from the conversation
    features = probes.evaluate(turns, vecs)

    # 5. Discover topics via clustering
    topics_list = topics.assign(turns, vecs)

    # 6. Perform Geo/Time planning
    # The payload doesn't contain a match location, so we pass None.
    geo_info = planner.compute(payload.ui_settings, payload.location, match_location=None)

    # 7. Pack context for the suggestion generator
    context_pack = ContextPack(
        turns=turns,
        features=features,
        topics=topics_list,
        geo=geo_info,
        compressed_history=None # Summarization is not implemented in this version
    )

    # 8. Generate raw suggestions from the context
    raw_suggestions = generator.suggest(context_pack)

    # 9. Rerank and enforce constraints on suggestions
    final_suggestions = reranker.enforce_constraints(raw_suggestions)

    # 10. Assemble the final, unified output object
    final_output = assembler.build(
        payload=payload,
        topics=topics_list,
        geo=geo_info,
        suggestions=final_suggestions,
        features=features
    )

    return final_output

if __name__ == '__main__':
    # Create a sample payload to demonstrate a pipeline run
    sample_payload = Payload(
        user_profile=UserProfile(user_id="u1", name="Alex"),
        match_profile=MatchProfile(match_id="m1", name="Sam"),
        location=Location(city="New York", country="USA"),
        ui_settings=UISettings(
            enhanced_nlp=True,
            local_model_config={},
            time_zone="America/New_York"
        ),
        conversation_history=[
            Message(role="user", text="Hey, how's it going?", timestamp="2024-01-01T12:00:00Z"),
            Message(role="match", text="Hey! Going great, just got back from a walk with my dog. You?", timestamp="2024-01-01T12:01:00Z"),
            Message(role="user", text="Nice! I love dogs. What kind do you have? I was thinking of getting a cat.", timestamp="2024-01-01T12:02:00Z"),
            Message(role="match", text="He's a golden retriever. So much energy! A cat sounds fun too, very chill. wink ;)", timestamp="2024-01-01T12:03:00Z"),
            Message(role="user", text="Haha, I bet! So, what are you passionate about?", timestamp="2024-01-01T12:04:00Z")
        ]
    )

    # Run the full analysis pipeline
    result = analyze_conversation(sample_payload)

    # Convert the final dataclass to a dictionary for clean JSON printing
    result_dict = dataclasses.asdict(result)

    print("--- Unified JSON Output ---")
    print(json.dumps(result_dict, indent=2))
