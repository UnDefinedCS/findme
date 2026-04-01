import math
import asyncio
from time import sleep, time
from urllib.parse import quote
from playwright.async_api import async_playwright

from app_types import UserData,SearchResult
from console_feedback import OK,ERR,INFO
from url_handler import extractGitHub

# change this to get more tabs
MAX_TABS = 5
VERBOSE = False

def generate_queries(data: UserData, verbose=False):
    global VERBOSE
    VERBOSE = verbose

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
    results = []

    url = f"https://duckduckgo.com/?q={quote(query)}&ia=web"
    await page.goto(url, wait_until="domcontentloaded")

    if "No results found" in await page.content():
        return True, results

    # load more results
    for _ in range(3):
        try:
            before = await page.locator(
                "article[data-testid='result']"
            ).count()

            await page.click("text=More Results")

            await page.wait_for_function(
                """prev => document.querySelectorAll(
                    "article[data-testid='result']"
                ).length > prev""",
                before,
                timeout=10000
            )

        except:
            break

    anchors = await page.query_selector_all(
        "a[data-testid='result-title-a']"
    )

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

async def collect_data(queries: list[str]) -> dict:
    if not queries:
        if (VERBOSE): print(f"{ERR} No Queries were Generated")
        return []

    print(f"{INFO} Generated {len(queries)} Search Queries")
    print("-" * 64)

    results_collection: list[SearchResult] = []

    find_times = []
    find_avg = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-gpu", "--disable-extensions", "--no-sandbox"])
        try:
            finished = 0
            for i in range(0, len(queries), MAX_TABS):
                q_group = [
                    q for q in queries[i:i + MAX_TABS]
                    if q.strip()
                ]

                if not q_group:
                    continue

                start_time = time()
                new_results = await send_queries(browser, q_group)
                batch_time = time() - start_time

                finished += len(q_group)

                find_times.append(batch_time)
                find_avg = sum(find_times) / len(find_times)

                results_collection.extend(new_results)

                remaining_queries = len(queries) - finished
                remaining_batches = math.ceil(remaining_queries / MAX_TABS)
                time_left = remaining_batches * find_avg

                mins, secs = divmod(int(time_left), 60)
                print(f"{INFO} Time Remaining: {mins}m {secs}s")
        finally:
            await browser.close()

    # map the results via a map where the URL is the key and the value is
    # a list of SearchResults because many queries can produce the same
    # URL target

    better_results = {}
    for entry in results_collection:
        url = entry["url"]

        # try extracting user profile from a github repo url
        if "//github.com/" in url:
            profile_url = extractGitHub(url)
            know_gh_profile = (profile_url in better_results)

            # if we extracted a profile, see if we arent already
            # tracking it in our url collection and move entrys
            # respectively
            if profile_url and know_gh_profile:
                better_results[profile_url].append(entry)
            elif profile_url and know_gh_profile == False:
                better_results[profile_url] = [entry]

        if url in better_results:
            better_results[url].append(entry)
        else:
            better_results[url] = [entry]
    return better_results