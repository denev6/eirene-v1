# API Server

The currently released code corresponds to the initial prototype (v1). To avoid influencing subsequent development, detailed components such as the database schema and prompt designs are not disclosed. If `USE_DUMMY_RESPONSE='true'` is set, the server can be tested regardless of the prompt configuration.

In later versions,

- v2: the counseling stages were redesigned to better align with clinical settings.
- v3: the system components were reconfigured through ablation studies.

## v1 Workflow Overview

![Overall workflow](/assets/flow.png)

## API Documentation

This API manages user counseling sessions, including session lifecycle management and streaming AI responses.

### Start Session

Initialize a new counseling session for a user.

- Endpoint: POST `/chat/start`
- Description: Generates a unique `session_id`. If the user is new, the session stage defaults to `SETTING`.
- Request Body:

    ```json
    {
      "user_id": "string"
    }
    ```

- Response:
  - 200 OK: ```{"session_id": "uuid-string"}```
  - 400 Bad Request: If session already exists and is active.

### Check Session

Verify the status and existence of an active session.

- Endpoint: POST `/chat/check`
- Description: Confirms if a session is valid and ready for interaction.
- Request Body:

    ```json
    {
      "session_id": "string"
    }
    ```

- Response:
  - 200 OK: ```{"status": "ready"}```
  - 404 Not Found: If the session ID does not exist.

### Chat (Streaming)

Send a message and receive a real-time AI response.

- Endpoint: POST `/chat`
- Description: Processes user input through a multi-agent system.
- Request Body:

    ```json
    {
      "session_id": "string",
      "message": "string"
    }
    ```

- Response:
  - StreamingResponse: A text/event-stream of the generated response chunks.
  - 404 Not Found: If the session ID is invalid.

### End Session

Terminate an active session and save progress.

- Endpoint: POST `/chat/end`
- Description: Updates the user's counseling stage in the database and clears the in-memory session store.
- Request Body:

    ```json
    {
      "session_id": "string"
    }
    ```

- Response:
  - 200 OK: ```{"message": "Session {session_id} ended."}```
  - 404 Not Found: If the session ID does not exist.
