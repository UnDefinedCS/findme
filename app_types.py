from typing import TypedDict

# type alias
class UserData(TypedDict):
    """
    { FirstName: str, LastName: str, Aliases: list[str] }
    """
    FirstName: str
    LastName: str
    Aliases: list[str]