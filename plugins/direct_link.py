#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#



import re
import cloudscraper
from bs4 import BeautifulSoup
from plugins.kwik import extract_kwik_link

#--------------------------------------------------direct_link.py-----------------------------------------#

def step_2(s, seperator, base=10):
    """Helper function for Kwik link bypass"""
    mapped_range = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
    numbers = mapped_range[0:base]
    max_iter = 0
    for index, value in enumerate(s[::-1]):
        max_iter += int(value if value.isdigit() else 0) * (seperator**index)
    mid = ''
    while max_iter > 0:
        mid = numbers[int(max_iter % base)] + mid
        max_iter = (max_iter - (max_iter % base)) / base
    return mid or '0'

def step_1(data, key, load, seperator):
    """First step in Kwik link bypass"""
    payload = ""
    i = 0
    seperator = int(seperator)
    load = int(load)
    while i < len(data):
        s = ""
        while data[i] != key[seperator]:
            s += data[i]
            i += 1
        for index, value in enumerate(key):
            s = s.replace(value, str(index))
        payload += chr(int(step_2(s, seperator, 10)) - load)
        i += 1
    payload = re.findall(
        r'action="([^\"]+)" method="POST"><input type="hidden" name="_token"\s+value="([^\"]+)', payload
    )[0]
    return payload

def bypass_kwik(link: str, scraper: cloudscraper.CloudScraper):
    """Bypass Kwik.si link to get direct download URL using cloudscraper"""
    try:
        resp = scraper.get(link)
        data, key, load, seperator = re.findall(r'\("(\S+)",\d+,"(\S+)",(\d+),(\d+)', resp.text)[0]
        url, token = step_1(data=data, key=key, load=load, seperator=seperator)
        data = {"_token": token}
        headers = {'referer': link}
        resp = scraper.post(url=url, data=data, headers=headers, allow_redirects=False)
        return resp.headers["location"]
    except Exception as e:
        print(f"Error bypassing Kwik link: {e}")
        return None

def get_dl_link(pahe_url: str):
    """Main function to get direct download link from Pahe.ph URL"""
    try:
        # Create cloudscraper instance that will be used for both requests
        scraper = cloudscraper.create_scraper()
        
        print("Extracting Kwik link from Pahe...")
        kwik_link = extract_kwik_link(pahe_url, scraper)
        if not kwik_link:
            return "Failed to extract Kwik link from Pahe.ph page"
        
        print(f"Found Kwik link: {kwik_link}")
        print("Bypassing Kwik link...")
        direct_link = bypass_kwik(kwik_link, scraper)
        
        if not direct_link:
            return "Failed to bypass Kwik.si link"
        
        return direct_link
    
    except Exception as e:
        return f"An error occurred: {str(e)}"
#----------------------------------------------------------------------------------------------------------------#

