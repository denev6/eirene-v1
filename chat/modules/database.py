import os
import sqlite3

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_naver import ClovaXEmbeddings

from .utils import logger


class VectorDB:
    def __init__(self, faiss_dir: str):
        self.embedding_model = ClovaXEmbeddings(
            model="bge-m3",
        )
        if os.path.exists(os.path.join(faiss_dir, "index.faiss")):
            self.index = FAISS.load_local(
                faiss_dir,
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True,
            )
        else:
            self.index = None
            logger.warning(f"{faiss_dir} not Found.")

        self.faiss_dir = faiss_dir

    def search(self, query: str, k: int = 3) -> list[Document]:
        if self.index is None:
            return []

        try:
            query_vec = np.array(
                self.embedding_model.embed_query(query), dtype=np.float32
            )
            query_vec /= np.linalg.norm(query_vec)
            return self.index.similarity_search_by_vector(query_vec, k=k)
        except Exception as e:
            logger.error(f"[VectorDB] {e}")
            return []


class UserSessionDB:
    def __init__(self, db_path):
        self.__counseling_session = {
            "SETTING",
            "PERCEPTION",
            "EMOTION",
            "ACCEPTANCE",
            "REMINISCENCE",
        }
        self.__conn = sqlite3.connect(db_path)
        self.__cursor = self.__conn.cursor()
        self.__cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id TEXT PRIMARY KEY,
                    session TEXT NOT NULL
                )
            """
        )
        self.__conn.commit()

    def close(self):
        self.__conn.close()

    def _assert_session(self, session_name: str) -> bool:
        session_name = str(session_name).strip().upper()
        if session_name in self.__counseling_session:
            return True
        return False

    def insert(self, user_id: str, session_name: str) -> bool:
        is_valid = self._assert_session(session_name)
        if not is_valid:
            logger.warning(
                f"[UserSessionDB] Invalid session injected: {session_name} ({user_id})"
            )
            return False

        try:
            self.__cursor.execute(
                "INSERT INTO user_sessions (user_id, session) VALUES (?, ?)",
                (user_id, session_name),
            )
            self.__conn.commit()
            logger.info(f"[UserSessionDB] Inserted {user_id}: {session_name}.")
            return True
        except sqlite3.IntegrityError:
            logger.error(
                f"[UserSessionDB] User ID {user_id} already exists. Cannot insert duplicate."
            )
            return False
        except sqlite3.Error as e:
            logger.error(f"[UserSessionDB] Error inserting user_id {user_id}: {e}")
            return False

    def update(self, user_id: str, session_name: str) -> bool:
        is_valid = self._assert_session(session_name)
        if not is_valid:
            logger.warning(
                f"[UserSessionDB] Invalid session: {session_name} ({user_id})"
            )
            return False

        try:
            self.__cursor.execute(
                "UPDATE user_sessions SET session = ? WHERE user_id = ?",
                (session_name, user_id),
            )
            self.__conn.commit()
            if self.__cursor.rowcount > 0:
                logger.info(
                    f"[UserSessionDB] Updated session for {user_id} to {session_name}."
                )
                return True
            else:
                logger.warning(
                    f"[UserSessionDB] User ID {user_id} not found for update."
                )
                return False
        except sqlite3.Error as e:
            logger.error(f"[UserSessionDB] Error updating user_id {user_id}: {e}")
            return False

    def delete(self, user_id: str) -> bool:
        try:
            self.__cursor.execute(
                "DELETE FROM user_sessions WHERE user_id = ?", (user_id,)
            )
            self.__conn.commit()
            if self.__cursor.rowcount > 0:
                logger.info(f"[UserSessionDB] Deleted user_id {user_id}.")
                return True
            else:
                logger.warning(
                    f"[UserSessionDB] User ID {user_id} not found for deletion."
                )
                return False
        except sqlite3.Error as e:
            logger.error(f"[UserSessionDB] Error deleting user_id {user_id}: {e}")
            return False

    def get(self, user_id: str) -> str | None:
        self.__cursor.execute(
            "SELECT session FROM user_sessions WHERE user_id = ?", (user_id,)
        )
        result = self.__cursor.fetchone()
        return result[0] if result else None
