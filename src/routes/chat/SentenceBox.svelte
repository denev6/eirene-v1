<script>
  let { speaker, sentence } = $props();
</script>

<div class="sentence-box {speaker}">
  <pre>{sentence}</pre>
</div>

<style>
  .sentence-box {
    padding: 8px;
    margin: 8px 16px;
    border-radius: 4px;
    max-width: 100%;
    box-sizing: border-box;
  }
  .sentence-box > pre {
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  .user {
    background-color: var(--gray-800);
    font-weight: bold;
    margin-top: 16px;
    padding: 10px 16px 8px;
  }
  .loading {
    animation: fadeAnimation 1.5s infinite alternate;
  }

  @keyframes fadeAnimation {
    0% {
      opacity: 0.2;
    }
    100% {
      opacity: 0.8;
    }
  }
</style>
