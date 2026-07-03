"""
Apollo.io Scraper - Apify Actor
Main entry point for the Apify Actor

This actor scrapes Apollo.io using a free account (no paid API required).
Works forever with free accounts - no credits needed!
"""

from apify import Actor
from src.scraper import ApolloScraper
from src.utils import log_message, is_valid_url
import json


async def main():
    """
    Main Apify Actor entrypoint.
    
    Gets input from Apify input, scrapes Apollo.io, and pushes results to dataset.
    """
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Validate required inputs
        apollo_cookies_raw = actor_input.get('apolloCookies')
        apollo_email = actor_input.get('apolloEmail')
        apollo_password = actor_input.get('apolloPassword')
        start_urls = actor_input.get('startUrls', [])
        
        # Parse cookies JSON string if provided
        apollo_cookies = None
        if apollo_cookies_raw:
            try:
                if isinstance(apollo_cookies_raw, str):
                    apollo_cookies = json.loads(apollo_cookies_raw)
                elif isinstance(apollo_cookies_raw, list):
                    apollo_cookies = apollo_cookies_raw
                log_message(f"✅ Parsed {len(apollo_cookies)} cookies from input", 'SUCCESS')
            except json.JSONDecodeError as e:
                log_message(f"⚠️  Failed to parse cookies JSON: {e}", 'WARNING')
                apollo_cookies = None
        
        # Require at least one auth method
        has_cookies = apollo_cookies and len(apollo_cookies) > 0
        has_credentials = apollo_email and apollo_password
        
        if not has_cookies and not has_credentials:
            raise ValueError(
                'Authentication required! Provide either:\n'
                '  1. apolloCookies - JSON array of browser cookies (RECOMMENDED)\n'
                '  2. apolloEmail + apolloPassword - Account credentials'
            )
        
        if not start_urls:
            raise ValueError('At least one start URL is required!')
        
        # Get configuration
        max_pages = actor_input.get('maxPages', 10)
        enrich_profiles = actor_input.get('enrichProfiles', True)
        min_delay = actor_input.get('minDelay', 3)
        max_delay = actor_input.get('maxDelay', 7)
        proxy_config = actor_input.get('proxyConfiguration')
        
        log_message(f"Starting Apollo scraper with {len(start_urls)} URLs")
        log_message(f"Max pages per URL: {max_pages}, Enrich profiles: {enrich_profiles}")
        
        # NOTE: Apollo.io detects Apify proxy - trying WITHOUT proxy first!
        # Get proxy URL if configured
        proxy_url = None
        use_proxy_option = False  # Force disable proxy for better success rate
        
        if proxy_config and use_proxy_option:  # Proxy disabled by default
            try:
                from apify import ProxyConfiguration
                # Create proxy configuration
                if isinstance(proxy_config, dict) and proxy_config.get('useApifyProxy'):
                    proxy_configuration = ProxyConfiguration()
                else:
                    proxy_configuration = ProxyConfiguration(**proxy_config) if isinstance(proxy_config, dict) else ProxyConfiguration()
                proxy_url = await proxy_configuration.new_url()
                log_message(f"Using proxy: {proxy_url[:50]}...")
            except Exception as e:
                log_message(f"Proxy setup failed, continuing without proxy: {e}", 'WARNING')
                proxy_url = None
        else:
            log_message("⚠️  Proxy DISABLED - Apollo.io blocks Apify proxy IPs", 'WARNING')
        
        # Initialize scraper
        scraper = None
        total_results = 0
        
        try:
            # Create scraper instance
            scraper = ApolloScraper(
                headless=True,  # Always headless on Apify
                use_proxy=proxy_url is not None,
                proxy_url=proxy_url
            )
            
            # Setup browser
            scraper.setup_driver()
            
            # Login to Apollo with cookie support
            log_message("🔐 Attempting to login to Apollo.io...")
            
            # Determine which cookies to use:
            # Priority: 1) User-provided input cookies  2) Saved KVS cookies
            login_cookies = None
            
            if apollo_cookies:
                # User provided cookies directly in the input
                login_cookies = apollo_cookies
                log_message(f"🍪 Using {len(login_cookies)} cookies from actor input", 'INFO')
            else:
                # Try to load saved cookies from Apify Key-Value Store
                try:
                    kvs = await Actor.open_key_value_store()
                    saved_cookies = await kvs.get_value('apollo_cookies')
                    if saved_cookies:
                        login_cookies = saved_cookies
                        log_message("✅ Found saved cookies in Key-Value Store", 'SUCCESS')
                    else:
                        log_message("⚠️  No saved cookies found, will use password login", 'WARNING')
                except Exception as e:
                    log_message(f"⚠️  Could not access Key-Value Store: {e}", 'WARNING')
            
            # Attempt login (will try cookies first if available)
            login_success = scraper.login(
                email=apollo_email,
                password=apollo_password,
                cookies=login_cookies
            )
            
            if not login_success:
                raise RuntimeError(
                    '❌ Login to Apollo.io failed!\n'
                    '💡 If using cookies: make sure they are fresh (not expired).\n'
                    '💡 If using email/password: check credentials or try cookie auth instead.'
                )
            
            # Save/update cookies to Key-Value Store for future runs
            if scraper.logged_in:
                try:
                    kvs = await Actor.open_key_value_store()
                    current_cookies = scraper.driver.get_cookies()
                    await kvs.set_value('apollo_cookies', current_cookies)
                    log_message("💾 Saved cookies to Key-Value Store for future runs", 'SUCCESS')
                    log_message("💡 TIP: Next run will use cookies and skip login!", 'INFO')
                except Exception as e:
                    log_message(f"⚠️  Could not save cookies: {e}", 'WARNING')
            
            # Process each URL
            for idx, url_obj in enumerate(start_urls):
                url = url_obj.get('url') if isinstance(url_obj, dict) else url_obj
                
                if not is_valid_url(url):
                    log_message(f"Skipping invalid URL: {url}", 'WARNING')
                    continue
                
                log_message(f"Processing URL {idx + 1}/{len(start_urls)}: {url}")
                
                try:
                    # Scrape the URL
                    results = scraper.scrape_url(
                        url=url,
                        follow_links=enrich_profiles,
                        max_pages=max_pages,
                        min_delay=min_delay,
                        max_delay=max_delay
                    )
                    
                    log_message(f"Scraped {len(results)} results from {url}", 'SUCCESS')
                    
                    # Push results to Apify dataset
                    if results:
                        await Actor.push_data(results)
                        total_results += len(results)
                    
                except Exception as e:
                    log_message(f"Error scraping {url}: {str(e)}", 'ERROR')
                    continue
            
            log_message(f"Scraping complete! Total results: {total_results}", 'SUCCESS')
            
        except Exception as e:
            log_message(f"Fatal error: {str(e)}", 'ERROR')
            raise
        
        finally:
            # Cleanup
            if scraper:
                scraper.close()
            
            log_message("Actor finished")


# Run the actor
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())


