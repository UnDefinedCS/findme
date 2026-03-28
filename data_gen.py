from bs4 import BeautifulSoup
from time import sleep
from playwright.async_api import async_playwright

from app_types import UserData

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
        queries.append(f"{data["FirstName"]} {service_provider}")
        queries.append(f"{username} {data["FirstName"]}")
        queries.append(f"{username} {data["FirstName"]} {service_provider}")
        queries.append(f"{username} {data["FirstName"]} {data["LastName"]}")
        queries.append(f"{username} {data["FirstName"]} {data["LastName"]} {service_provider}")

    return queries