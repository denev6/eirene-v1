import os
import re
import time
import requests
from bs4 import BeautifulSoup


def parse(url, target, css_selector, header=""):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.select_one(css_selector)

    if element:
        if target.lower() == "a":
            a_tags = element.find_all("a", href=True)
            urls = [a["href"] for a in a_tags]
            print(urls)

        else:
            text = element.get_text(strip=False)
            text = text.replace("\xa0", " ")
            text = re.sub(r"\n+", "\n", text)
            text = re.sub(r"[ \t]+", " ", text)
            text = text.strip()

            output = "output/" + header + url.split("/")[-1] + ".txt"
            os.makedirs(os.path.dirname(output), exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(text)

            print("Saved at", output)

    else:
        print("No elements found.")


if __name__ == "__main__":
    urls = [...]

    css_selector = "#main-content > article > div > div.cgdpl"
    target = ""  # 'a' or ''

    for url in urls:
        try:
            parse(url, target, css_selector, header="side-effects-")
        except Exception as e:
            print(url, e)
        time.sleep(0.1)
