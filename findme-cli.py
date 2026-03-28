from app_types import UserData
from data_gen import generate_queries, collect_data

import asyncio

INFO = "[\033[34m!\033[0m] INFO:"
ERR = "[\033[31m-\033[0m] ERROR:"
OK = "[\033[32m+\033[0m] OK:"

def print_all(data: UserData):
   print(data["FirstName"])
   print(data["LastName"])
   print(data["Aliases"])

def list_aliases():
    aliases = []
    print(f"{INFO} Format: alias,[github,reddit,twitter,...]")
    print(" |___ Example: ihatewindows11,reddit\n") # give spacing between the new info
    print(f"{INFO} When finished press Enter to continue.")

    while True:
        data = str(input("Online Alias: ")).strip()
        if data == "":
            return aliases
        
        alias = data.split(",")
        if len(alias) == 1:
            # username and no known connections
            aliases.append([data,None])
        if len(alias) == 2:
            # username with one linked alias
            aliases.append(alias)
        elif len(alias) > 2:
            # same username with multiple connections
            for i in range(1,len(alias)):
                aliases.append([alias[0],alias[i]])

def prompt():
    print(f"{INFO} Enter All Inputs Comma Seperated")
    print(f" |__ To not provide input press ENTER")
    nameData = str(input("First,Last Name: ")).strip()
    firstName = nameData
    lastName = None
    
    if "," in nameData:
        firstName,lastName = nameData.split(',')

    aliases = list_aliases()
    
    data: UserData = {
        "FirstName": firstName,
        "LastName": lastName,
        "Aliases": aliases
    }

    #print_all(data)
    queries = generate_queries(data)
    asyncio.run(collect_data(queries))

def main():
    prompt()

if __name__ == "__main__":
    main()