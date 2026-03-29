import asyncio
from time import sleep
from urllib.parse import quote
from playwright.async_api import async_playwright

from app_types import UserData
from console_feedback import OK,ERR,INFO

def generate_queries(data: UserData):
    queries: list[str] = []

    fName = data["FirstName"].strip()
    lName = data["LastName"].strip()
    target_ctx = data["Context"]

    if (fName):
        queries.append(fName)
        
    if (lName):
        queries.append(lName)

    if (fName and lName):
        queries.append(f'{fName} {lName}')
        queries.append(f'"{fName} {lName}"')
        queries.append(f'"{lName}, {fName}"')
        queries.append(f'"{fName} {lName}" site:linkedin.com') # explicitly look for linkedin

    # focus on the alias
    for username,platform in data["Aliases"]:
        queries.append(username)
        if (platform):
            queries.append(f"{username} {platform.lower()}")

    # apply context
    for ctx in target_ctx:
        if (fName):
            queries.append(f'"{fName}" {ctx}')
        if (lName):
            queries.append(f'"{lName}" {ctx}')
        if (fName and lName and ctx):
            queries.append(f'"{fName} {lName}" {ctx}')
            queries.append(f'{fName} {lName} {ctx}')

    # mix alias, name, and ctx
    for username,platform in data["Aliases"]:
        service_provider = platform.lower() if platform else None
        
        if (fName):
            queries.append(f"{fName} {username}")

        if (fName and lName):
            queries.append(f"{username} {fName} {lName}")

        if (fName and lName and service_provider):
            queries.append(f"{username} {fName} {lName} {service_provider}")

        if (service_provider and fName):
            queries.append(f"{fName} {service_provider}")
            
        if (service_provider and fName):
            queries.append(f"{username} {fName} {service_provider}")

        for ctx in target_ctx:
            queries.append(f"{username} {ctx}")

    return queries

async def search_duckduckgo(page, query: str):
    results: list[dict] = []

    url = f"https://duckduckgo.com/?q={quote(query)}&ia=web"
    await page.goto(url)

    content = await page.content()

    if "No results found" in content:
        print(f"{INFO} No results from search -> {query}")
        return True, results

    if "we ran into an error" in content:
        print(f"{INFO} Retrying query -> {query}")
        return False, results

    try:
        ol = await page.wait_for_selector(
            "ol.react-results--main", timeout=60000
        )
        print(f"{INFO} Found Results List -> {query}")
    except:
        print(f"{ERR} No results list or blocked -> {query}")
        return True, results

    anchors = await ol.query_selector_all(
        "article[data-testid='result'] a[data-testid='result-title-a']"
    )

    if not anchors:
        print(f"{INFO} No anchor elements -> {query}")
        return True, results

    for a in anchors:
        href = await a.get_attribute("href")
        title = await a.inner_text()

        results.append({
            "query": query,
            "url": href,
            "site_title": title
        })

    return True, results


async def send_queries(browser, queries: list[str]) -> list[dict]:
    pages = [await browser.new_page() for _ in queries]
    tasks = [
        asyncio.create_task(search_duckduckgo(pages[i], queries[i]))
        for i in range(len(queries))
    ]

    results: list[dict] = []
    try:
        for task in asyncio.as_completed(tasks):
            success, data = await task
            if success: results.extend(data)
    finally:
        for page in pages:
            await page.close()
    return results

async def collect_data(queries: list[str]) -> list[dict]:
    if not queries:
        print(f"{ERR} No Queries were Generated")
        return []

    print(f"{INFO} Query Count -> {len(queries)}")
    print("-" * 64)

    results_collection = []

    # change this to get more tabs
    MAX_TABS = 5
    
    # safety bounds checking
    if MAX_TABS <= 0:
        MAX_TABS = 5

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--window-position=-2400,-2400',  # Move window off-screen
                '--window-size=1,1'  # Minimize window size
            ]
        )
        try:
            for i in range(0, len(queries), MAX_TABS):
                q_group = [
                    q for q in queries[i:i + MAX_TABS]
                    if q.strip()
                ]

                if not q_group:
                    continue

                new_results = await send_queries(browser, q_group)
                results_collection.extend(new_results)
        finally:
            await browser.close()
    return results_collection