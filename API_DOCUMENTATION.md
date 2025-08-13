# Frontend API Documentation

This document provides the necessary information for a frontend application to interact with the Wingman AI backend API.

***

## 1. Health Check Endpoint

This endpoint can be used to verify that the backend service is running.

*   **Endpoint:** `GET /health`
*   **Method:** `GET`
*   **Description:** Provides a simple health check for the service.
*   **Request Body:** None.

---
**Sample Response (`200 OK`)**
```json
{
  "status": "ok",
  "version": "8.0.0"
}
```

***

## 2. Full Conversation Analysis Endpoint

This is the primary endpoint for starting a new session or performing a full analysis of a conversation.

*   **Endpoint:** `POST /api/v1/analyze`
*   **Method:** `POST`
*   **Description:** Performs a full analysis of a conversation, saves the state to the database, and returns the complete analysis object along with an initial set of prompts based on smart defaults.

---
**Sample Request Body**
```json
{
  "matchId": "match-12345",
  "myName": "Alex",
  "myProfile": "28, software engineer. I enjoy hiking, trying new craft beers, and sci-fi movies.",
  "theirName": "Brianna",
  "theirProfile": "26, graphic designer. Loves art museums, live music, and her golden retriever, Max.",
  "theirLocationString": "Brooklyn, NY",
  "conversationHistory": [
    {
      "role": "assistant",
      "content": "Hey! I saw you're into live music, what's the best show you've seen recently?",
      "date": "2023-10-26T10:00:00Z"
    },
    {
      "role": "user",
      "content": "Oh wow, tough question! Probably The National last month, it was amazing.",
      "date": "2023-10-26T10:05:00Z"
    }
  ],
  "ui_settings": {
    "myLocation": "Manhattan, NY"
  }
}
```

---
**Sample Response (`200 OK`)**
*Note: The `full_analysis` object is very large and complex. This is a simplified example.*
```json
{
  "prompts": {
    "system_prompt": "You are DateWing, an AI ghostwriter...",
    "user_prompt": "--- CONVERSATIONAL LANDSCAPE & STRATEGY ---\n... \n--- YOUR MISSION: BUILD_RAPPORT --- \n...",
    "model_name": null,
    "temperature": 0.7,
    "top_p": 1,
    "token_count": 482
  },
  "full_analysis": {
    "conversationState": "ACTIVE_CONVO",
    "conversationPacing": "fast",
    "strategicGoal": {
      "type": "BUILD_RAPPORT",
      "justification": "The conversation is active. Continue building connection and positive sentiment.",
      "urgency": "normal"
    },
    "memory": {
      "investmentScore": 0.3,
      "rapportScore": 0.6,
      "sexualTension": 0.1,
      "isLongDistance": false
    }
  },
  "applied_ui_settings": {
    "flirtyValue": 50,
    "lengthValue": 50,
    "linguisticStyle": "auto",
    "humorStyle": "witty",
    "endWithQuestion": true
  }
}
```

***

## 3. Regenerate Prompts Endpoint

This endpoint is used to get new prompts after the user changes a UI setting, without re-running the full, expensive analysis.

*   **Endpoint:** `POST /api/v1/regenerate`
*   **Method:** `POST`
*   **Description:** Regenerates prompts using a previously completed analysis (loaded from the database) but with new, user-provided UI settings. **This endpoint returns only the prompt object.**

---
**Sample Request Body**
*Note: The `scraped_data` is still required to provide context for the prompt generation.*
```json
{
  "matchId": "match-12345",
  "scraped_data": {
    "myName": "Alex",
    "myProfile": "28, software engineer...",
    "theirName": "Brianna",
    "theirProfile": "26, graphic designer...",
    "conversationHistory": [
        { "role": "assistant", "content": "...", "date": "..."}
    ]
  },
  "ui_settings": {
    "flirtyValue": 80,
    "lengthValue": 30,
    "linguisticStyle": "playful",
    "humorStyle": "goofy",
    "endWithQuestion": false,
    "customInstruction": "Mention her dog, Max."
  }
}
```

---
**Sample Response (`200 OK`)**
*This endpoint now returns only the prompt object, making it more lightweight.*
```json
{
  "system_prompt": "You are DateWing, an AI ghostwriter...",
  "user_prompt": "--- CONVERSATIONAL LANDSCAPE & STRATEGY ---\n... \n--- YOUR MISSION: ESCALATE_FLIRT --- \n...",
  "model_name": null,
  "temperature": 0.7,
  "top_p": 1,
  "token_count": 510
}
```

***

## 4. Get All Options Endpoint

This endpoint provides all the necessary information to dynamically build the UI controls for the application.

*   **Endpoint:** `GET /api/v1/options/all`
*   **Method:** `GET`
*   **Description:** Returns a comprehensive, categorized list of all selectable options and parameters supported by the backend.
*   **Request Body:** None.

---
**Sample Response (`200 OK`)**
*This is a shortened example. The actual response contains many more parameters and groups.*
```json
[
  {
    "groupName": "UI Controls",
    "groupDescription": "Settings that directly control the generated message style and content.",
    "parameters": [
      {
        "name": "flirtyValue",
        "description": "Controls the level of flirtatiousness...",
        "valueType": "integer",
        "defaultValue": 50,
        "uiType": "slider",
        "constraints": { "min": 0, "max": 100, "step": 1 }
      },
      {
        "name": "linguisticStyle",
        "description": "Determines the linguistic style of the generated message.",
        "valueType": "string",
        "defaultValue": "auto",
        "uiType": "dropdown",
        "constraints": {
          "allowedValues": [
            { "value": "auto", "description": "Auto" },
            { "value": "casual", "description": "Casual" }
          ]
        }
      },
      {
        "name": "endWithQuestion",
        "description": "If checked, the generated message will end with a question...",
        "valueType": "boolean",
        "defaultValue": true,
        "uiType": "checkbox",
        "constraints": null
      }
    ]
  },
  {
    "groupName": "Conversation Analysis Thresholds",
    "groupDescription": "Advanced settings to fine-tune how the AI analyzes conversational dynamics...",
    "parameters": [
      {
        "name": "INVESTMENT_SCORE_DECAY_FACTOR",
        "description": "The rate at which the investment score decays over time...",
        "valueType": "float",
        "defaultValue": 0.8,
        "uiType": "slider",
        "constraints": { "min": 0.5, "max": 1, "step": 0.05 }
      }
    ]
  }
]
```
