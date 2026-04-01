from app_types import UserData
from data_gen import generate_queries, collect_data
from data_analyze import review

import asyncio
from console_feedback import OK,ERR,INFO

VERBOSE = False

def print_all(data: UserData):
   print(data["FirstName"])
   print(data["LastName"])
   print(data["Aliases"])

def list_aliases():
    aliases = []
    print(f"{INFO} Enter All Inputs Comma Seperated")
    print(f"{INFO} Format: alias,[github,reddit,twitter,...]")
    print(" |___ Example: ihatewindows11,reddit or iluwlinux,github,reddit")
    print(" |___ Press Enter to Continue\n")

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
                aliases.append([alias[0].strip(), alias[i].strip()])

def list_context() -> list[str]:
    print(f"{INFO} Enter All Inputs Comma Seperated")
    print(f"{INFO} What is the target context?")
    print(" |___ Example: Kent State or Kent State, Alumni")
    print(" |___ Press Enter to Continue\n")
    
    ctx = []
    while True:
        ctx_data = str(input("Target Context: "))
        if ctx_data == "": break
        ctx.append(ctx_data.strip())

    if len(ctx) == 0:
        print(f"{INFO} No Context Given")
        print(" |___ Results may contain many false-positives")

    return ctx

def save_results(results):
    if results is None: return
    if len(results) == 0: return

    save_data = str(input("Do you want to save [y/N]: ")).lower().strip()
    if len(save_data) == 0:
        return
    elif save_data == "n" or save_data == "no":
        return
    
    file_name = ""
    while len(file_name) == 0:
        file_name = str(input("File Name: "))

    with open(file_name,"w") as outFile:
        for r,s in results:
            if s == -1:
                outFile.write(f"[+] | {r['query']} -> {r['url']}\n")
            else:
                outFile.write(f"[+] Score -> {s} | {r['query']} -> {r['url']}\n")

async def prompt():
    print(f"{INFO} Enter All Inputs Comma Seperated")
    print(f"{INFO} To not provide input press ENTER")
    firstName = input("First Name: ")
    lastName = input("Last Name: ")

    # most times having a first/last name is not enough information (too vague)
    if firstName or lastName:
        print(f"\n{INFO} Recommanded: Add either an alias or context, otherwise you may get little to no results.")

    aliases = list_aliases()

    target_ctx = list_context()

    # handle no inputs
    if not firstName and not lastName and not aliases and not target_ctx:
        print(f"{INFO} No input was given, nothing to search")
        return
    
    data: UserData = {
        "FirstName": firstName.strip() if lastName else None,
        "LastName": lastName.strip() if lastName else None,
        "Aliases": aliases,
        "Context": target_ctx
    }

    global VERBOSE
    queries = generate_queries(data, VERBOSE)
    result_data = await collect_data(queries)
    output = None
    if len(result_data) > 0:
        output = await review(data, result_data, False, VERBOSE)
    print(f"{OK} Scanning Finished!")
    print(" |___ Results are not guaranteed to be 100% accurate, user must manually evaluate")
    save_results(output)

import argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show Verbose Output"
    )
    parser.add_argument(
        "--data-removal",
        action="store_true",
        help="Learn how to remove your data"
    )
    args = parser.parse_args()
    
    if args.data_removal:
        print("""
How can I remove my data from these search results?

Connections to accounts are often made due to hard-coded linking, this can be from simple social media account linking to hardcoding a url on your website.

It is recommended to use multiple usernames and to try as best as possible to never allow your accounts to cross paths, for certain websites you can control your visibility, it is recommended to set this to private where search engines when they try going to your links return a 404 not found.
You can request Google or other Engine Providers to remove a search result from their feed if a url leads to a 404 as it will be considered a dead-link. Avoid posting sensitive information on social media as it can be saved and made extremely difficult to remove, ensure your images you post
do not carry location meta-data from your mobile phone camera or show potential artifacts that can be used to figure out where the image was taken if near your residence.
""")
    else:
        global VERBOSE
        VERBOSE = args.verbose
        asyncio.run(prompt())

if __name__ == "__main__":
    main()