import requests
import time
import sys

SERVER_URL = "http://127.0.0.1:8001"
MAX_CHECK_ITER = 3
headers = {"accept": "application/json", "Content-Type": "application/json"}


def send_request(url, json):
    response = requests.post(url=f"{SERVER_URL}{url}", headers=headers, json=json)
    return response


def stream_request(url, json):
    print("Q:", json["message"])
    print("A:", end=" ")

    try:
        response_time = None
        start_time = time.time()

        with requests.post(
            url=f"{SERVER_URL}{url}", headers=headers, json=json, stream=True
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=512):
                if chunk:
                    if response_time is None:
                        response_time = time.time()
                    print(chunk.decode("utf-8"), flush=True, end="")
            end_time = time.time()
            print("\n", end="")

        print(f"Response time: {response_time - start_time:.3f}(s)")
        print(f"Execution time: {end_time - start_time:.3f}(s)")

    except Exception as e:
        print(e, "\n")


# Input User ID
user_id = input("User ID: ")
if user_id == "":
    print("User ID is empty!")
    sys.exit(1)


# Connect to API Server
response = send_request(
    url="/chat/start",
    json={
        "user_id": user_id,
    },
)
session_id = response.json()["session_id"]
print(f"Current session: {session_id}")

is_ready = False
for _ in range(MAX_CHECK_ITER):
    response = send_request(
        url="/chat/check",
        json={
            "session_id": session_id,
        },
    )
    if response.status_code == 200:
        is_ready = True
        break
    time.sleep(2)

if not is_ready:
    print("Session is not ready.")
    sys.exit(2)

try:
    # Ask Eirene
    print("\n================================")
    user_message = input("Ask Eirene (Enter to exit): ")
    while user_message.strip():
        stream_request(
            url="/chat",
            json={"session_id": session_id, "message": user_message},
        )
        print("\n================================")
        user_message = input("Ask Eirene (Enter to exit): ")

except Exception as e:
    print("\n\n{e}\n")

finally:
    # End session
    send_request(
        url="/chat/end",
        json={
            "session_id": session_id,
        },
    )
