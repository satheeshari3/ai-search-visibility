import httpx
from bs4 import BeautifulSoup

from app.services.crawler import fetch_page, extract_page_data

url = "https://docs.python.org/3/license.html"

soup = fetch_page(url)
data = extract_page_data(soup)

print("TITLE:", data["title"])
print("\nHEADINGS:", data["headings"])
print("\nEXTRACTED TEXT PREVIEW:\n")


print("\nMAIN CONTENT CHECKS:")
for phrase in [
    "asyncio",
    "Examples",
    "License",
    "Copyright",
]:
    print(f"{phrase}: {phrase.lower() in data['text'].lower()}")

print("\nCHECKS:")
print("Contains theme controls:", "Theme Auto Light Dark" in data["text"])
print("Contains navigation label:", "Table of Contents" in data["text"])
print("Extracted text length:", len(data["text"]))