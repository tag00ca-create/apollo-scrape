"""
Configuration management for Apollo scraper Apify Actor.
"""

class Config:
    """Central configuration class for Apollo scraper"""
    
    # Scraping settings
    MIN_DELAY = 3
    MAX_DELAY = 7
    MAX_RETRIES = 3
    PAGE_LOAD_TIMEOUT = 30
    
    # Apollo URLs
    APOLLO_LOGIN_URL = 'https://app.apollo.io/#/login'
    APOLLO_BASE_URL = 'https://app.apollo.io'
    
    # Browser settings - DESKTOP-ONLY user agents for rotation (must match Chrome version on Apify)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'
    ]
    
    # Pagination limits
    MAX_PAGES = 100
    RESULTS_PER_PAGE = 25
    
    @classmethod
    def get_random_user_agent(cls):
        """Get a random user agent from the list"""
        import random
        return random.choice(cls.USER_AGENTS)





