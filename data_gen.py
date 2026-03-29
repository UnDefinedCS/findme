import asyncio
from time import sleep
from urllib.parse import quote
from playwright.async_api import async_playwright

from app_types import UserData, SearchResult
from console_feedback import OK,ERR,INFO

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

    return queries

async def search_duckduckgo(query: str) -> {bool, list[SearchResult]}:
    async with async_playwright() as p:
        # at this time it must not be headless or the list cannot be located
        # for unknown reason
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        results: list[SearchResult] = []

        url = f"https://duckduckgo.com/?q={quote(query)}&ia=web"
        await page.goto(url)

        # check the contents of the page after search
        content = await page.content()
        if "No results found" in content:
            print(f"{INFO} No results from search")
            await browser.close()
            return True, results
    
        # an error occurred, rerun the query incase it is a network problem
        # resolved via reloading
        if "we ran into an error" in content:
            print(f"{INFO} Retrying query")
            await browser.close()
            return False, results

        try:
            ol = await page.wait_for_selector("ol.react-results--main", timeout=60000)
            print(f"{INFO} Found Results List!")
        except:
            print(f"{ERR} No results found or page blocked!")
            await browser.close()
            return True, results

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
        return True, results

async def collect_data(queries: list[str]) -> list[SearchResult]:
    if (len(queries) == 0):
        print(f"{ERR} No Queries were Generated")
        return []

    print(f"{INFO} Query Count -> {len(queries)}")
    print("-" * 64)

    results_collection: list[SearchResult] = []
    for q in queries:
        # check if query is an empty string and ignore it
        if not q.strip(): continue

        print(f"Searching -> {q}")
        attempt = 0
        success, new_results = await search_duckduckgo(q)
        
        # allow for limited retries (dont enter infinite retry loop give up at some point)
        while not success and attempt < 5:
            attempt += 1
            success, new_results = await search_duckduckgo(q)

        results_collection += new_results
    print(f"{OK} Total: {len(results_collection)}")
    print("-" * 64)
    return results_collection