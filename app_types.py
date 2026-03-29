from typing import TypedDict

# type alias
class UserData(TypedDict):
    """
    { FirstName: str, LastName: str, Aliases: list[str] }
    """
    FirstName: str
    LastName: str
    Aliases: list[str]
    Context: list[str]

class SearchResult(TypedDict):
    """
    { query: str, url: str, site_title: str }
    """
    query: str
    url: str
    site_title: str