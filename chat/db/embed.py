import html
import time
import re
import glob
import os
from typing import List, Dict, Any

import backoff
import numpy as np
from tqdm import tqdm
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_naver import ClovaXEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv("../../.env")

MEDICAL_DB_FAISS = "chat/db/medical_vector_db"
LEGACY_DB_FAISS = "chat/db/legacy_vector_db"

embedding_model_bge = ClovaXEmbeddings(model="bge-m3")


def _create_documents(
    content: str, metadata: Dict[str, Any], chunk_size: int, chunk_overlap: int
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    docs = []
    chunks = text_splitter.split_text(content)
    for chunk in chunks:
        doc = Document(page_content=chunk, metadata=metadata)
        docs.append(doc)
    return docs


@backoff.on_exception(backoff.expo, Exception, max_tries=10, jitter=backoff.full_jitter)
def _create_embeddings(texts: List[str]) -> List[List[float]]:
    return embedding_model_bge.embed_documents(texts)


def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def _embed_documents(
    documents: List[Document],
    faiss_dir: str,
):
    if not documents:
        return

    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    embeddings = []

    for i in range(0, len(texts), 5):
        batch = texts[i : i + 5]
        emb = _create_embeddings(batch)
        embeddings.extend(emb)
        time.sleep(3)

    embeddings_np = _normalize_embeddings(embeddings)
    text_embeddings = list(zip(texts, embeddings_np))

    if os.path.exists(os.path.join(faiss_dir, "index.faiss")):
        faiss_index = FAISS.load_local(
            faiss_dir,
            embeddings=embedding_model_bge,
            allow_dangerous_deserialization=True,
        )
        faiss_index.add_embeddings(text_embeddings=text_embeddings, metadatas=metadatas)
    else:
        faiss_index = FAISS.from_embeddings(
            text_embeddings=text_embeddings,
            metadatas=metadatas,
            embedding=embedding_model_bge,
        )

    faiss_index.save_local(folder_path=faiss_dir)


def _remove_html(raw_text: str) -> str:
    decoded_text = html.unescape(raw_text)
    clean_text = re.sub(r"<[^>]+>", "", decoded_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text


def embed_legacy_db():
    txt_files_path = os.path.join("../legacy_db_utils", "*.txt")
    txt_files = glob.glob(txt_files_path)
    total_items = len(txt_files)
    print(f"{total_items} files found in {txt_files_path}")

    for idx, file_path in tqdm(enumerate(txt_files)):
        docs = []

        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read().strip()

        sections = re.findall(r"## (.+?)\n(.*?)(?=\n## |\Z)", contents, re.DOTALL)
        contents = [(title.strip(), content.strip()) for title, content in sections]

        for title, content in contents:
            metadata = {"title": title}
            docs.extend(
                _create_documents(content, metadata, chunk_size=1000, chunk_overlap=100)
            )

        _embed_documents(docs, LEGACY_DB_FAISS)
        tqdm.write(f"[{idx + 1}/{total_items}] Embedded '{file_path}'.")

    print(f"Finish embedding document(s) at {LEGACY_DB_FAISS}.")


def medical_legacy_db():
    txt_files_path = os.path.join("../medical_db_utils", "korean", "*.txt")
    txt_files = glob.glob(txt_files_path)
    total_items = len(txt_files)
    print(f"{total_items} files found in {txt_files_path}")

    for idx, file_path in tqdm(enumerate(txt_files)):
        label = os.path.basename(file_path).rstrip(".txt")

        with open(file_path, "r", encoding="utf-8") as f:
            to_embed = f.read().strip()
        metadata = {"label": label}

        docs = _create_documents(to_embed, metadata, chunk_size=1000, chunk_overlap=100)

        _embed_documents(docs, MEDICAL_DB_FAISS)
        tqdm.write(f"[{idx + 1}/{total_items}] Embedded '{label}'.")

    print(f"Finish embedding document(s) at {MEDICAL_DB_FAISS}.")


if __name__ == "__main__":
    # Example
    os.environ["CLOVASTUDIO_API_KEY"] = os.getenv("CLOVASTUDIO_API_KEY")
    embed_legacy_db()
