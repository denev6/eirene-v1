import glob
import os
import time

from dotenv import load_dotenv
from langchain_naver import ChatClovaX
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv("../.env")

os.environ["CLOVASTUDIO_API_KEY"] = os.getenv("CLOVASTUDIO_API_KEY")

SYSTEM_PROMPT = """\
당신은 전문 의학 번역가입니다. 영어로 작성된 의학 문서를 한국어로 정확하고 충실하게 번역하는 역할을 수행합니다.

다음 지침을 반드시 따르세요:

1. 모든 의학 용어는 정확하게 번역하며, 가능한 경우 한글 뒤에 영문 원어를 괄호 안에 병기하십시오.  
   예: 신장암(Kidney cancer)
2. 다음과 같은 문장은 번역 대상에서 제외하고 출력하지 마십시오:
   - 인용 출처: “Updated <MM/DD/YYYY>. Available at: ...”, “Accessed <MM/DD/YYYY>”, 또는 PMID가 포함된 문장
   - 이미지 출처: “Credit: © ...”, “Enlarge Image”와 같은 문장
   - 연락 요청: “E-mail Us.”와 같은 문장
3. 의역이나 요약 없이 원문의 의미와 문장 구조를 최대한 그대로 유지하여 번역하십시오.
4. 번역 품질은 의료 전문가가 읽을 수 있는 수준으로 정밀해야 하며, 내용의 누락이나 왜곡이 없어야 합니다.
5. 번역 결과만 출력합니다.
"""

USER_PROMPT = """다음 영어 의학 문서를 위 지침에 따라 한국어로 번역해 주세요:
"""

llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=4096)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=0)


folder_path = "output"
target_path = "korean"
os.makedirs(target_path, exist_ok=True)
txt_files = glob.glob(os.path.join(folder_path, "*.txt"))

for file_path in txt_files:
    file_name = os.path.basename(file_path)
    target_file_path = os.path.join(target_path, file_name)

    with open(file_path, "r", encoding="utf-8") as f:
        doc = f.read()

    translated = []
    is_exception_occurred = False
    chunks = text_splitter.split_text(doc)

    for chunk in chunks:
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT + chunk + "\n\n번역:"},
                ]
            )
        except Exception:
            is_exception_occurred = True
            time.time(5)

        translated.append(response.content.strip())

    translated_doc = " ".join(translated)
    with open(f"{target_file_path}", "w", encoding="utf-8") as f:
        f.write(translated_doc)

    if is_exception_occurred:
        print(f"=== Exception while {file_name}")
    else:
        print(f"Translated {file_name}")
