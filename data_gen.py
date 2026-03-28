import asyncio
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import quote
from playwright.async_api import async_playwright

from app_types import UserData

INFO = "[\033[34m!\033[0m] INFO:"
ERR = "[\033[31m-\033[0m] ERROR:"
OK = "[\033[32m+\033[0m] OK:"

def generate_queries(data: UserData):
    queries = [
        f"{data["FirstName"]} {data["LastName"]}",
    ]

    # focus on the alias
    for username,platform in data["Aliases"]:
        queries.append(username)
        queries.append(f"{username} {platform.lower()}")

    # mix alias and name
    for username,platform in data["Aliases"]:
        service_provider = platform.lower()
        queries.append(f"{data["FirstName"]} {username}")

        if (service_provider):
            queries.append(f"{data["FirstName"]} {service_provider}")
            
        queries.append(f"{username} {data["FirstName"]}")
        if (service_provider):
            queries.append(f"{username} {data["FirstName"]} {service_provider}")

        if (data["LastName"]):
            queries.append(f"{username} {data["FirstName"]} {data["LastName"]}")
        if (data["LastName"]):
            queries.append(f"{username} {data["FirstName"]} {data["LastName"]} {service_provider}")

    print(f"{INFO} Query Count -> {len(queries)}")
    return queries

async def search_duckduckgo(query: str):
    async with async_playwright() as p:
        # at this time it must not be headless or the list cannot be located
        # for unknown reason
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = f"https://duckduckgo.com/?q={quote(query)}&ia=web"
        await page.goto(url)

        try:
            ol = await page.wait_for_selector("ol.react-results--main", timeout=60000)
            print(f"{INFO} Found Results List!")
        except:
            print(f"{ERR} No results found or page blocked!")
            await browser.close()
            return

        anchors = await ol.query_selector_all(
            "article[data-testid='result'] a[data-testid='result-title-a']"
        )

        if not anchors:
            print(f"{INFO} No anchor elements found!")
        else:
            for a in anchors:
                href = await a.get_attribute("href")
                text = await a.inner_text()
                print(f"Title -> {text}")
                print(f"URL   -> {href}")
                print()

        await browser.close()

async def collect_data(queries: list[str]):
    print(f"[!] INFO: Query Count -> {len(queries)}")
    print("-" * 64)

    for q in queries:
        print(f"Searching -> {q}")
        await search_duckduckgo(q)

    print("-" * 64)