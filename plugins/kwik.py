#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#
import re
import cloudscraper
from bs4 import BeautifulSoup


#-----------------------------------kwik.py-------------------------------------------------------------#
def extract_kwik_link(pahe_url: str, scraper: cloudscraper.CloudScraper):
    """Extract Kwik.si link from Pahe.ph page using cloudscraper"""
    try:
        response = scraper.get(pahe_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check both script tags and iframes for kwik links
        for element in soup.find_all(['script', 'iframe']):
            if element.name == 'script' and element.get('type') == 'text/javascript':
                match = re.search(r'https://kwik\.si/f/[\w\d]+', element.text)
            else:
                match = re.search(r'https://kwik\.si/f/[\w\d]+', str(element))
            if match:
                return match.group(0)
        
        return None
    
    except Exception as e:
        print(f"Error extracting Kwik link from Pahe: {e}")
        return None
#-------------------------------------------------------------------------------------------------#
