import asyncio
from playwright.async_api import async_playwright

from app_types import UserData, SearchResult
from console_feedback import OK,ERR,INFO

def site_contains(page_content:str, target_str):
    if not target_str: return False
    return target_str.lower() in page_content

async def check_site_content(page, base_data:UserData, url: str):
    global site_cache, ignore_cache

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

        acceptable_confidence = 2.5 + (len(aliases) * 0.3)
        result = "Accepted" if confidence >= acceptable_confidence else "Invalid"

        print(f"{INFO} Confidence [{result}] {confidence:.2f} -> {url}")
        return confidence >= acceptable_confidence, confidence
    except Exception as e:
        print(f"{ERR} Url most likely timed out")
        return False,-1

site_cache: list[str] = []
ignore_cache: list[str] = []
BATCH_SIZE = 15
async def run_batch(browser, base_data, batch):
    pages = [await browser.new_page() for _ in batch]
    tasks = [
        check_site_content(pages[i], base_data, batch[i]["url"])
        for i in range(len(batch))
    ]

    results = await asyncio.gather(*tasks)
    for page in pages:
        await page.close()

    return results

async def review(base_data: UserData, results: list[SearchResult]):
    global site_cache, ignore_cache

    print(f"{INFO} Reviewing Discovered Data")
    print(f" |___ number of results: {len(results)}")

    acceptable_confidence = 2.5 + (len(base_data["Aliases"]) * 0.3)
    print(f"{INFO} Acceptable Level: {acceptable_confidence}")

    filtered_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for i in range(0, len(results), BATCH_SIZE):
                batch = results[i:i + BATCH_SIZE]
                batch_results = await run_batch(browser, base_data, batch)

                for result, (high_confidence, score) in zip(batch, batch_results):
                    url = result["url"]
                    if high_confidence:
                        site_cache.append(url)
                        filtered_results.append((result,score))
                    else:
                        if score != -1 and score <= 0.5:
                            ignore_cache.append(url)
        finally:
            await browser.close()

    print(f"{INFO} Filtered Results: {len(results)} -> {len(filtered_results)}")
    print("-" * 64)
    for r,s in filtered_results:
        if s == -1:
            print(f"{OK} | {r['query']} -> {r['url']}")
        else:
            print(f"{OK} Score -> {s} | {r['query']} -> {r['url']}")
    print("-" * 64)
    return filtered_results