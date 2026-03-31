import math
import time
import asyncio
from playwright.async_api import async_playwright

from app_types import UserData
from console_feedback import OK,ERR,INFO

# change this to run more confidence checks concurrently
BATCH_SIZE = 20
VERBOSE = False
FROM_FLASK = True

from sys import stdout
done_count = 0
SEARCH_SIZE = 0
avg_batch_time = None
batch_times = []

def site_contains(page_content:str, target_str):
    if not target_str: return False
    return target_str.lower() in page_content

def print_progress():
    if FROM_FLASK:
        return
    
    global done_count
    done_count += 1

    if (VERBOSE == False):
        # clear current line
        stdout.write("\r\033[K")
        stdout.flush()

        bar_width = 30
        filled = int((done_count / SEARCH_SIZE) * bar_width)
        prog_str = "=" * filled + " " * (bar_width - filled)
        stdout.write(f"[{prog_str}] {done_count}/{SEARCH_SIZE}")
        if avg_batch_time != None:
            remaining_urls = SEARCH_SIZE - done_count
            remaining_batches = math.ceil(remaining_urls / BATCH_SIZE)
            time_left = remaining_batches * avg_batch_time

            mins, secs = divmod(int(time_left), 60)
            stdout.write(f" | Time Remaining: {mins}m {secs}s")
        stdout.flush()

async def check_site_content(page, base_data:UserData, target):
    global site_cache
    global ignore_cache

    global batch_times
    global avg_batch_time

    url, searches = target

    # init checking
    if url in ignore_cache:
        return False,-1
    
    if url in site_cache:
        return True,-1

    fName = base_data["FirstName"]
    lName = base_data["LastName"]
    aliases = base_data["Aliases"]
    context = base_data["Context"]

    try:
        start_time = time.time()

        # networkidle | domcontentloaded
        await page.goto(url, wait_until="networkidle", timeout=10000)
        content = await page.inner_text("body")
        
        if not content:
            return False,-1
        
        content = content.lower()

        # overal site confidence (very crude and can be improved with a LLM)
        confidence = 0

        hasFName = site_contains(content, fName)
        hasLName = site_contains(content, lName)

        if hasFName and hasLName:
            confidence += 2
        else:
            if hasFName:
                confidence += 0.5
            if hasLName:
                confidence += 0.5

        alias_score = 0

        for username, provider in aliases:
            username = username.lower()
            if (provider):
                provider = provider.lower()

            has_user = site_contains(content, username)
            has_provider = site_contains(content, provider)

            if has_user and has_provider:
                alias_score += 3
            elif has_user:
                alias_score += 2
            elif has_provider:
                alias_score += 0.5

        alias_score = min(alias_score, 4)
        confidence += alias_score

        ctx_score = 0

        for ctx in context:
            ctx = ctx.lower()

            if site_contains(content, ctx):
                ctx_score += 1
                continue

            for word in ctx.split():
                if len(word) < 4:
                    continue
                if site_contains(content, word):
                    ctx_score += 0.2

        ctx_score = min(ctx_score, 2)
        confidence += ctx_score

        # avoid extreme number increase from many aliases
        acceptable_confidence = (2.5 + (len(aliases) * 0.3)) if (2.5 + (len(aliases) * 0.3)) < 3 else 3
        result = "\033[32mAccepted\033[0m" if confidence >= acceptable_confidence else "Invalid"

        batch_duration = time.time() - start_time

        batch_times.append(batch_duration)
        avg_batch_time = sum(batch_times) / len(batch_times)

        print_progress()

        # show positive hits
        if (confidence >= acceptable_confidence or VERBOSE):
            stdout.write("\n")
            stdout.flush()
            print(f"{INFO} Confidence [{result}] {confidence:.2f} -> {url}")
        
        return confidence >= acceptable_confidence, confidence
    except Exception as e:
        if (VERBOSE): print(f"{ERR} Url most likely timed out")
        print_progress()
        return False,-1

site_cache: list[str] = []
ignore_cache: list[str] = []
async def run_batch(browser, base_data, batch):
    pages = [await browser.new_page() for _ in batch]
    tasks = [
        check_site_content(pages[i], base_data, batch[i])
        for i in range(len(batch))
    ]

    # collection of (true|false, confidence_score)
    results = await asyncio.gather(*tasks)
    for page in pages:
        await page.close()

    return results

async def review(base_data: UserData, results: dict, using_flask=True, verbose=False) -> list:
    global VERBOSE,FROM_FLASK
    VERBOSE = verbose
    FROM_FLASK = using_flask
    
    global site_cache, ignore_cache, SEARCH_SIZE

    print(f"{INFO} Reviewing Discovered Data")
    print(f" |___ Total URLs Found: {len(results)}")

    # avoid extreme number increase from many aliases
    acceptable_confidence = (2.5 + (len(base_data["Aliases"]) * 0.3)) if (2.5 + (len(base_data["Aliases"]) * 0.3)) < 3 else 3

    if (VERBOSE):
        print(f"{INFO} Acceptable Level: {acceptable_confidence}")

    # convert the dict into an iterable object
    # [ ( "example.com", [obj1, obj2, ...] ), ... ]
    search_group = list(results.items())
    filtered_results = []

    SEARCH_SIZE = len(search_group)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-gpu", "--disable-extensions", "--no-sandbox"])
        try:
            for i in range(0, len(search_group), BATCH_SIZE):
                batch = search_group[i:i + BATCH_SIZE]
                batch_results = await run_batch(browser, base_data, batch)

                for search_target, (high_confidence, score) in zip(batch, batch_results):
                    # query_group is a list of dictionarys
                    url, query_group = search_target
                    if high_confidence:
                        site_cache.append(url)
                        filtered_results.append((query_group,score))
                    else:
                        if score != -1 and score <= 0.5:
                            ignore_cache.append(url)
            stdout.write("\n")
            stdout.flush()
        finally:
            await browser.close()

    print(f"{INFO} Filtered URLs: {len(results)} -> {len(filtered_results)}")
    print("-" * 64)
    for q_group, score in filtered_results:
        for r in q_group:
            if score == -1:
                print(f"{OK} | {r['query']} -> {r['url']}")
            else:
                print(f"{OK} Score -> {score} | {r['query']} -> {r['url']}")
    print("-" * 64)
    return filtered_results