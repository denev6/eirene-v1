<script>
  import { goto } from "$app/navigation";
  import { startChatSession, checkChatSession } from "$lib/client_api.js";

  let userId = "";
  let isLoading = false;
  let errorMessage = "";

  async function handleSubmit() {
    isLoading = true;
    errorMessage = "";
    try {
      const startResponse = await startChatSession(userId);
      const sessionId = startResponse.session_id;

      if (sessionId) {
        sessionStorage.setItem("sessionId", sessionId);
        sessionStorage.setItem("userId", userId);

        const poll = async () => {
          try {
            await checkChatSession(sessionId);
            goto("/chat");
          } catch (error) {
            setTimeout(poll, 2000);
          }
        };
        poll();
      } else {
        errorMessage = "Failed to start chat session. Please try again.";
        isLoading = false;
      }
    } catch (error) {
      errorMessage = error.message || "An unknown error occurred.";
      isLoading = false;
    }
  }
</script>

<main>
  <h1>사용자 ID</h1>
  <form on:submit|preventDefault={handleSubmit}>
    <input
      type="text"
      bind:value={userId}
      placeholder="abcd1234"
      disabled={isLoading}
    />
    <button type="submit" disabled={isLoading}>
      {isLoading ? "연결..." : "확인"}
    </button>
  </form>
  {#if errorMessage}
    <p class="error">{errorMessage}</p>
  {/if}
</main>

<style>
  h1 {
    text-align: center;
    margin-top: 64px;
    margin-bottom: 48px;
  }
  form {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    justify-content: center;
    margin: 8px;
  }
  input {
    padding: 8px 12px;
    border: 0px;
    border-radius: 4px;
    background-color: var(--gray-800);
    color: var(--text);
    font-size: 17px;
  }
  input:focus {
    outline: none;
    background-color: var(--gray-700);
  }
  button {
    background-color: var(--primary-700);
    color: var(--text);
    padding: 8px 12px;
    border: 0px;
    border-radius: 4px;
    font-size: 17px;
  }
  button:hover {
    cursor: pointer;
    background-color: var(--primary-300);
  }
  .error {
    color: red;
    margin-top: 1rem;
  }
</style>
