# Offline-First Conversation Analysis Engine

This project implements a sophisticated, offline-first conversation analysis pipeline. It processes conversation histories to extract features, topics, and engagement metrics, ultimately generating context-aware suggestions. The entire system is designed to run on a local machine without internet access, prioritizing privacy and performance.

## Key Features

- **Fully Offline:** All models and services are designed to run locally.
- **Intimacy & Engagement-Aware:** The pipeline analyzes signals like flirtation, reciprocity, and disclosure to gauge the conversation's tone and engagement level.
- **Context-Aware Suggestions:** Generates talking points, questions, and next-action plans based on the conversation's context, topics, and time of day.
- **Efficient & Scalable:** Uses quantized models (simulation), caching, and an efficient vector index (FAISS HNSW) to ensure fast response times (target < 15s).
- **Modular Architecture:** The system is broken down into clean, single-responsibility services, making it easy to maintain and extend.

## Module / Service Layout

```
app/
├── main.py           # Main pipeline orchestrator
├── schemas.py        # Data structures for the application
├── data/             # (Placeholder for data caches, logs)
├── index/            # (Placeholder for FAISS index files)
├── models/           # (Placeholder for ML models)
├── probes/           # (Placeholder for probe models)
├── prompts/          # (Placeholder for LLM prompt templates)
└── svc/
    ├── assembler.py
    ├── embedder.py
    ├── generator.py
    ├── index.py
    ├── normalizer.py
    ├── planner.py
    ├── probes.py
    ├── reranker.py
    └── topics.py
```

## How to Run

1.  **Install Dependencies:**
    Install the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Pipeline:**
    Execute the main pipeline script from the root directory of the project. The `-m` flag is important as it tells Python to run the `app` directory as a module.
    ```bash
    python3 -m app.main
    ```
    This will run the pipeline with a sample conversation payload and print the resulting analysis and suggestions as a JSON object to the console.

## Output Schema

The pipeline produces a detailed JSON object that provides a holistic view of the conversation. The main keys are:

-   **`matchId`**: The unique identifier for the conversation.
-   **`conversation_state`**: Contains categorized topics (`focus`, `avoid`, `sensitive`, `sexual`, etc.) and a list of recent topics.
-   **`geo`**: Provides detailed geo-spatial and temporal information for both the user and the match, including local time of day, timezone differences, and whether the interaction is virtual.
-   **`suggestions`**: Offers context-aware recommendations, including topics to discuss, questions to ask, and suggestions for building sexual or emotional intimacy.
-   **`analysis`**: A comprehensive analysis of the conversation's dynamics, including the match's engagement level, comfort level, flirtation level, and other stylistic metrics.
-   **`sentiment`**: A high-level sentiment analysis of the conversation.
-   **`pipeline`**: The name and version of the analysis pipeline used.

## Pipeline Overview

The system processes data in the following sequence:

1.  **Normalize & Clean:** Input text is cleaned, and the conversation history is truncated.
2.  **Generate Embeddings:** Cleaned text is converted into numerical vectors (embeddings).
3.  **Index & Search:** Embeddings are stored in a FAISS HNSW index for efficient similarity search.
4.  **Feature Probes:** A rule-based engine evaluates the text for signals like questions, flirtation, and engagement.
5.  **Topic Discovery:** Embeddings are clustered to identify the main topics of conversation.
6.  **Geo/Time Planning:** The user's local time of day is calculated.
7.  **Generate Suggestions:** A mock LLM (rule-based generator) creates suggestions based on all the collected context.
8.  **Rerank & Assemble:** Suggestions are filtered and limited, and all data is assembled into a final JSON output.
