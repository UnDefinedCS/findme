import asyncio
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import quote
from playwright.async_api import async_playwright

from app_types import UserData, SearchResult

INFO = "[\033[34m!\033[0m] INFO:"
ERR = "[\033[31m-\033[0m] ERROR:"
OK = "[\033[32m+\033[0m] OK:"

def generate_queries(data: UserData):
    queries: list[str] = []

    fName = data["FirstName"]
    lName = data["LastName"]

    if (fName):
        queries.append(fName)
        
    if (lName):
        queries.append(lName)

    if (fName and lName):
        queries.append(f'"{fName} {lName}"')
        queries.append(f'"{lName}, {fName}"')
        queries.append(f'"{fName} {lName}" site:linkedin.com') # explicitly look for linkedin

    # focus on the alias
    for username,platform in data["Aliases"]:
        queries.append(username)
        if (platform):
            queries.append(f"{username} {platform.lower()}")

    # mix alias and name
    for username,platform in data["Aliases"]:
        service_provider = platform.lower() if platform else None
        
        if (fName):
            queries.append(f"{fName} {username}")

        if (service_provider and fName):
            queries.append(f"{fName} {service_provider}")
            
        if (service_provider and fName):
            queries.append(f"{username} {fName} {service_provider}")

        if (lName and lName):
            queries.append(f"{username} {fName} {lName}")

        if (lName and lName and service_provider):
            queries.append(f"{username} {fName} {lName} {service_provider}")

    print(f"{INFO} Query Count -> {len(queries)}")
    return queries

async def search_duckduckgo(query: str):
    async with async_playwright() as p:
        # at this time it must not be headless or the list cannot be located
        # for unknown reason
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        results: list[SearchResult] = []

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
                title = await a.inner_text()
                results.append({
                    "query": query,
                    "url": href,
                    "site_title": title
                })

        await browser.close()
        return results

async def collect_data(queries: list[str]):
    print(f"[!] INFO: Query Count -> {len(queries)}")
    print("-" * 64)

    results_collection: list[SearchResult] = []
    for q in queries:
        print(f"Searching -> {q}")
        results_collection += await search_duckduckgo(q)
    print(f"{OK} Total: {len(results_collection)}")
    for r in results_collection:
        print(f" |__ {r['query']} -> {r['site_title']} <- {r['url']}")
    print("-" * 64)