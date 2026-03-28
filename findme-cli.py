from typing import TypedDict

INFO = "[\033[34m!\033[0m] INFO:"
ERR = "[\033[31m-\033[0m] ERROR:"
OK = "[\033[32m+\033[0m] OK:"

# type alias
class UserData(TypedDict):
    FirstName: str
    LastName: str
    Aliases: list[str]

def print_all(data: UserData):
   print(data["FirstName"])
   print(data["LastName"])
   print(data["Aliases"])

def list_aliases():
    aliases = []
    print(f"{INFO} Format: alias,[github,reddit,twitter,...]")
    print(" |___ Example: ihatewindows11,reddit")
    print(f"{INFO} Enter DONE to continue.")

    while True:
        data = str(input("Online Alias: ")).strip()
        if data == "DONE":
            return aliases
        
        alias = data.split(",")
        if len(alias) == 2:
            aliases.append(alias)
        elif len(alias) > 2:
            aliases.append([alias[0],alias[1]])

def prompt():
    print(f"{INFO} Enter All Inputs Comma Seperated")
    firstName,lastName = str(input("Full Name: ")).strip().split(' ')
    aliases = list_aliases()
    
    data: UserData = {
        "FirstName": firstName,
        "LastName": lastName,
        "Aliases": aliases
    }
    print_all(data)

def main():
    prompt()

if __name__ == "__main__":
    main()