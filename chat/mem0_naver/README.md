# Mem0-Naver

This project is a modified version of the `mem0` library, adapted to integrate with `langchain-naver` and `FAISS`.

The original project was forked from [mem0ai/mem0](https://github.com/mem0ai/mem0) (v0.1.114).

## Overview

`Mem0-Naver` provides an intelligent, self-improving memory layer for AI applications. It enables AI to remember past conversations and information, allowing for more personalized and context-aware interactions. This version utilizes Naver's powerful language model (ClovaX) and embedding models to perform its core functions.

The main prompts are located in `mem0_naver/configs/prompts.py`.

## Key Features

- **LLM Integration**: Uses `ChatClovaX` from `langchain-naver` to process and generate memories.
- **Embedding Model**: Utilizes `ClovaXEmbeddings` to convert text into high-quality vectors.
- **Vector Store**: Employs `FAISS`, a high-performance local vector database, to store and retrieve memories without needing a separate server.
- **Easy Configuration**: The memory system can be configured with a simple dictionary-based setup.

## Setup and Usage

The following is an example of how to set up and initialize a `Memory` instance.

```python
import os
from langchain_naver import ChatClovaX, ClovaXEmbeddings
from dotenv import load_dotenv

from mem0_naver import Memory, AsyncMemory

# Load environment variables from .env file
load_dotenv()

# Set Clova Studio API key
os.environ["CLOVASTUDIO_API_KEY"] = os.getenv("CLOVASTUDIO_API_KEY")

# Mem0 Configuration
config = {
    # Language Model (LLM) Configuration
    "llm": {
        "provider": "langchain",
        "config": {
            # Use Naver ClovaX model
            "model": ChatClovaX(model="HCX-005", temperature=0, max_tokens=2048)
        },
    },
    # Embedding Model Configuration
    "embedder": {
        "provider": "langchain",
        "config": {
            # Use Naver ClovaX embedding model
            "model": ClovaXEmbeddings(model="clir-emb-dolphin")
        },
        "embedding_dims": 1024, # Embedding dimensions
    },
    # Vector Store Configuration
    "vector_store": {
        "provider": "faiss", # Use FAISS
        "config": {
            "collection_name": "ltm", # Collection name
            "distance_strategy": "inner_product", # Based on 'clir-emb-dolphin'
            "path": "./db/faiss_ltm", # Storage path
            "embedding_model_dims": 1024 # Embedding dimensions
        },
    },
    "version": "v1.1",
}

# Create a Memory instance from the config object
# For synchronous usage:
memory = Memory.from_config(config)

# For asynchronous usage:
# async_memory = await AsyncMemory.from_config(config)

# Now you can use the memory object to add or search for memories.
# Example: memory.add("Content to remember", user_id="user123")
# Example: memory.search("Content to search", user_id="user123")
```
