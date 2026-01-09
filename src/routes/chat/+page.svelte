<script>
  import { onMount, tick } from "svelte";
  import { goto } from "$app/navigation";
  import { sendChatMessage, endChatSession } from "$lib/client_api.js";
  import arrowIcon from "$lib/assets/arrow-up.svg";
  import SentenceBox from "./SentenceBox.svelte";

  let userMessage = "";
  let is_loading = false;
  let conversations = [];
  let sessionId;
  let userId;
  let textareaElement;

  onMount(() => {
    sessionId = sessionStorage.getItem("sessionId");
    userId = sessionStorage.getItem("userId");
    if (!sessionId || !userId) {
      goto("/");
    }
  });

  async function askLLM() {
    if (is_loading || !userMessage.trim()) {
      return;
    }
    is_loading = true;

    const messageToSend = userMessage;
    conversations = [...conversations, ["user", messageToSend]];
    userMessage = "";

    conversations = [...conversations, ["loading", "생각 중..."]];
    requestAnimationFrame(scrollToBottom);

    let responseMessage = "";
    const onChunk = (chunk) => {
      responseMessage += chunk;
      if (
        conversations.length > 0 &&
        conversations[conversations.length - 1][0] === "loading"
      ) {
        // Replace loading message with the first chunk
        conversations = [
          ...conversations.slice(0, -1),
          ["llm", responseMessage],
        ];
      } else if (
        conversations.length > 0 &&
        conversations[conversations.length - 1][0] === "llm"
      ) {
        // Update the last message with the new chunk
        conversations[conversations.length - 1][1] = responseMessage;
        conversations = [...conversations]; // Svelte reactivity
      }
      scrollToBottom();
    };

    try {
      await sendChatMessage(sessionId, userId, messageToSend, onChunk);
      // If the stream ends and the loading message is still there, it means the response was empty.
      if (
        conversations.length > 0 &&
        conversations[conversations.length - 1][0] === "loading"
      ) {
        conversations = conversations.slice(0, -1);
      }
    } catch (error) {
      console.error("Error during chat:", error);
      const errorMsg = "오류: 요청을 받을 수 없는 상태입니다.";
      if (
        conversations.length > 0 &&
        conversations[conversations.length - 1][0] === "loading"
      ) {
        conversations = [...conversations.slice(0, -1), ["llm", errorMsg]];
      } else if (
        conversations.length > 0 &&
        conversations[conversations.length - 1][0] === "llm"
      ) {
        conversations[conversations.length - 1][1] = errorMsg;
      } else {
        conversations = [...conversations, ["llm", errorMsg]];
      }
    } finally {
      is_loading = false;
      conversations = [...conversations]; // Ensure UI is updated
      // Automatically focuses the textarea for continuous user input
      await tick();
      if (textareaElement) {
        textareaElement.focus();
      }
    }
  }

  async function handleEndSession() {
    try {
      await endChatSession(sessionId);
    } catch (error) {
      console.error("Error ending session:", error);
    } finally {
      sessionStorage.removeItem("sessionId");
      sessionStorage.removeItem("userId");
      goto("/");
    }
  }

  function handleKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      if (!is_loading) {
        event.preventDefault();
        askLLM();
      }
    }
  }

  function scrollToBottom() {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: "smooth",
    });
  }
</script>

<svelte:document onkeydown={handleKeydown} />

<div class="header">
  <button class="end-session-button" onclick={handleEndSession}
    >대화 종료</button
  >
</div>

<div id="floating-box">
  <div id="input-container">
    <textarea
      id="input-area"
      bind:this={textareaElement}
      bind:value={userMessage}
      placeholder="질문을 적어주세요."
      disabled={is_loading}
    ></textarea>
    <button onclick={askLLM} onkeydown={handleKeydown} disabled={is_loading}>
      <img src={arrowIcon} alt="submit" />
    </button>
  </div>
</div>
<div id="conversation-container">
  {#each conversations as conversation, i}
    <SentenceBox speaker={conversation[0]} sentence={conversation[1]} />
  {/each}
</div>

<style>
  .header {
    position: fixed;
    top: 0;
    right: 0;
    padding: 12px;
    z-index: 1000;
    width: 100%;
    background: linear-gradient(
      180deg,
      var(--gray-900) 0%,
      rgba(37, 37, 37, 0.8) 100%
    );
  }

  .end-session-button {
    float: right;
    padding: 8px 16px;
    background-color: var(--primary-900);
    font-size: 15px;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .end-session-button:hover {
    background-color: var(--primary-700);
  }
  #floating-box {
    position: fixed;
    left: 50%;
    bottom: 16px;
    transform: translate(-50%, 0);
    width: 95%;
    text-align: center;
  }
  #input-container {
    background-color: var(--gray-800);
    border-radius: 8px;
    display: flex;
    align-items: flex-end;
    padding: 12px 8px 8px 16px;
  }
  textarea {
    flex-grow: 1;
    padding: 4px;
    font-size: 18px;
    line-height: 1.3;
    color: var(--text-dimmed);
    background-color: transparent;
    border: none;
    height: 60px;
    resize: none;
    overflow-y: auto;
    outline: none;
    font-family: inherit;
  }
  button {
    display: flex;
    justify-content: center;
    align-items: center;
    color: var(--gray-300);
    background-color: var(--primary-700);
    font-size: 24px;
    padding: 4px;
    border: none;
    border-radius: 50%;
    margin-left: 10px;
    cursor: pointer;
    align-self: flex-end;
    white-space: nowrap;
  }
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  #conversation-container {
    margin-top: 4rem; /* Adjust to avoid overlap with the header */
    margin-bottom: 160px;
  }
</style>
