from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app_types import UserData, SearchResult
from console_feedback import OK,ERR,INFO

async def review(base_data:UserData, results: list[SearchResult]):
    print(f"{INFO} Reviewing Discovered Data")
    for result in results:
        print(f" |__ {result['query']} -> {result['site_title']} <- {result['url']}")