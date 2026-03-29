from app_types import UserData
from data_gen import generate_queries, collect_data
from data_analyze import review

import asyncio
from console_feedback import OK,ERR,INFO

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
                aliases.append([alias[0].strip(), alias[i].strip()])

def list_context() -> list[str]:
    print(f"{INFO} What is the target context?")
    print(" |___ Press Enter to Continue")
    
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
    print(f" |__ To not provide input press ENTER")
    nameData = str(input("First,Last Name: ")).strip()
    firstName = nameData
    lastName = None
    
    if "," in nameData:
        firstName,lastName = nameData.split(',')

    aliases = list_aliases()

    target_ctx = list_context()
    
    data: UserData = {
        "FirstName": firstName.strip(),
        "LastName": lastName.strip(),
        "Aliases": aliases,
        "Context": target_ctx
    }

    #print_all(data)
    queries = generate_queries(data)
    result_data = await collect_data(queries)
    output = await review(data, result_data)
    print(f"{OK} Scanning Finished!")
    save_results(output)

def main():
    asyncio.run(prompt())

if __name__ == "__main__":
    main()