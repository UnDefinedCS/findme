def extractGitHub(url:str):
    base_site = "//github.com/"
    pos = url.find(base_site)
    chunks = url[pos+len(base_site):].split("/")
    
    profile_url = "https://github.com/" + str(chunks[0])
    found_profile = (profile_url != "https://github.com/")

    return profile_url if found_profile else None