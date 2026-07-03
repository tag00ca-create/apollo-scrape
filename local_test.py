import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.scraper import ApolloScraper
from src.segmenter import SearchSegmenter
from src.parser import parse_apollo_search_url
import json

async def main():
    print("?? Starting Local Test")
    
    # URL that user tried (Egypt)
    url = "https://app.apollo.io/#/people?page=1&personLocations[]=egypt&recommendationConfigId=score&sortByField=%5Bnone%5D&sortAscending=false"
    
    scraper = None
    try:
        # Load local cookies
        cookies_path = r"e:\apollo\cookies.json"
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
            
        scraper = ApolloScraper(headless=False)  # Non-headless for local debugging
        
        login_success = scraper.login(cookies=cookies)
        if not login_success:
            print("? Login failed")
            return
            
        print("? Login successful")
        
        # Test Segmentation
        parsed = parse_apollo_search_url(url)
        segmenter = SearchSegmenter()
        segments = segmenter.generate_segments(level='deep', filters=parsed['filters'])
        print(f"?? Generated {len(segments)} segments")
        
        # Scrape just the first segment for testing
        if segments:
            segment = segments[0]
            print(f"?? Testing Segment: {segment['label']}")
            seg_url = scraper._build_search_url(segment['filters'], 1)
            
            results = scraper.scrape_url(
                url=seg_url,
                follow_links=False,
                max_pages=1,
                min_delay=3,
                max_delay=5
            )
            
            if results:
                print(f"?? Successfully scraped {len(results)} records!")
                print(json.dumps(results[0], indent=2))
            else:
                print("?? No results returned")
                
    except Exception as e:
        print(f"? Error: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
