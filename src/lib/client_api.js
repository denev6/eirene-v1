const BASE_URL = "http://localhost:8001"; // Assuming the FastAPI server runs at this URL.

/**
 * Starts a new chat session.
 * @param {string} userId - The ID of the user starting the session.
 * @returns {Promise<object>} - A promise that resolves with the API response.
 */
async function startChatSession(userId) {
  try {
    const response = await fetch(`${BASE_URL}/chat/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to start session.");
    }
    return response.json();
  } catch (error) {
    console.error("Error starting chat session:", error);
    throw error;
  }
}

/**
 * Checks the status of a chat session.
 * @param {string} sessionId - The ID of the session to check.
 * @returns {Promise<object>} - A promise that resolves with the API response.
 */
async function checkChatSession(sessionId) {
  try {
    const response = await fetch(`${BASE_URL}/chat/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to check session status.");
    }
    return response.json();
  } catch (error) {
    console.error("Error checking chat session:", error);
    throw error;
  }
}

/**
 * Sends a message to a chat session and streams the response.
 * @param {string} sessionId - The ID of the session.
 * @param {string} userId - The ID of the user sending the message.
 * @param {string} message - The user's message.
 * @param {function} onChunk - The callback function to handle each chunk of the streamed response.
 * @returns {Promise<void>} - A promise that resolves when the streaming is complete.
 */
async function sendChatMessage(sessionId, userId, message, onChunk) {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_id: userId,
        message: message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to send message.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        // 서버에서 chunk 끝에 '\n'을 붙여서 stream함
        onChunk(chunk);
      }
    }
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
}

/**
 * Ends a chat session.
 * @param {string} sessionId - The ID of the session to end.
 * @returns {Promise<object>} - A promise that resolves with the API response.
 */
async function endChatSession(sessionId) {
  try {
    const response = await fetch(`${BASE_URL}/chat/end`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to end session.");
    }
    return response.json();
  } catch (error) {
    console.error("Error ending chat session:", error);
    throw error;
  }
}

// Export functions for external use
export { startChatSession, checkChatSession, sendChatMessage, endChatSession };
