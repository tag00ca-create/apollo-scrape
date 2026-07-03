"""
Core scraping logic for Apollo.io with ADVANCED ANTI-DETECTION
Uses undetected-chromedriver and multiple stealth techniques to bypass bot detection.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import random
import json
from typing import List, Dict, Optional, Any
from faker import Faker

from src.config import Config
from src.utils import random_delay, retry_on_failure, log_message, is_valid_url
from src.parser import (
    parse_search_results, parse_contact_profile,
    parse_company_profile, detect_page_type,
    parse_apollo_search_url, flatten_api_response,
    get_pagination_info
)


class ApolloScraper:
    """Advanced Apollo.io scraper with anti-detection capabilities"""
    
    def __init__(self, headless: bool = True, use_proxy: bool = False, proxy_url: str = None):
        """
        Initialize the Apollo scraper with anti-detection.
        
        Args:
            headless: Run browser in headless mode (Note: headless is more detectable)
            use_proxy: Use proxy settings
            proxy_url: Proxy URL to use
        """
        self.driver = None
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.logged_in = False
        self.faker = Faker()
        self.cookies = None
        
    def _detect_chrome_version(self) -> Optional[int]:
        """Detect the installed Chrome major version to match ChromeDriver."""
        import subprocess
        import re
        
        chrome_commands = [
            ['google-chrome', '--version'],
            ['google-chrome-stable', '--version'],
            ['chromium', '--version'],
            ['chromium-browser', '--version'],
        ]
        
        for cmd in chrome_commands:
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
                match = re.search(r'(\d+)\.', output)
                if match:
                    version = int(match.group(1))
                    log_message(f"🔍 Detected Chrome version: {version} (from '{output}')", 'INFO')
                    return version
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                continue
        
        log_message("⚠️  Could not detect Chrome version, letting uc auto-detect", 'WARNING')
        return None
    
    def setup_driver(self):
        """Setup undetected-chromedriver with advanced anti-detection"""
        log_message("Setting up undetected ChromeDriver (anti-detection mode)...", 'INFO')
        
        # Detect installed Chrome version to avoid version mismatch
        chrome_version = self._detect_chrome_version()
        
        # Prepare options for undetected-chromedriver
        options = uc.ChromeOptions()
        
        # Note: Headless mode is MORE detectable. Only use if absolutely necessary.
        if self.headless:
            options.add_argument('--headless=new')
            log_message("⚠️  Running in headless mode (more detectable)", 'WARNING')
        else:
            log_message("✅ Running in headful mode (less detectable)", 'INFO')
        
        # Use a realistic DESKTOP user agent (Faker generates mobile UAs which Apollo rejects)
        user_agent = Config.get_random_user_agent()
        options.add_argument(f'user-agent={user_agent}')
        log_message(f"Using user agent: {user_agent[:60]}...", 'DEBUG')
        
        # Essential stealth arguments
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Disable automation flags
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # Language settings (looks more human)
        options.add_argument('--lang=en-US,en;q=0.9')
        options.add_argument('--accept-lang=en-US,en;q=0.9')
        
        # Proxy configuration
        if self.use_proxy and self.proxy_url:
            options.add_argument(f'--proxy-server={self.proxy_url}')
            log_message(f"✅ Using proxy: {self.proxy_url[:50]}...", 'INFO')
        else:
            log_message("⚠️  No proxy configured - Apollo may block datacenter IPs", 'WARNING')
        
        # Additional prefs to avoid detection
        # Wrapped in try/except because some uc versions handle these internally
        try:
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            options.add_experimental_option("prefs", prefs)
        except Exception as e:
            log_message(f"⚠️  Could not set experimental options (uc may handle them): {e}", 'DEBUG')
        
        try:
            # Initialize undetected-chromedriver
            # This automatically patches ChromeDriver to avoid detection
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,  # Better for avoiding detection
                version_main=chrome_version,  # Match installed Chrome version
                driver_executable_path=None,  # Let uc find it
            )
            
            # Set page load timeout
            self.driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
            
            # Additional stealth measures
            self._inject_advanced_stealth()
            
            log_message("✅ Undetected ChromeDriver setup complete!", 'SUCCESS')
            
        except Exception as e:
            log_message(f"❌ Failed to setup undetected-chromedriver: {e}", 'ERROR')
            raise
    
    def _inject_advanced_stealth(self):
        """Inject advanced JavaScript to further hide automation"""
        stealth_js = """
        // Advanced stealth script - handles multiple detection vectors
        
        // 1. Remove webdriver property
        try {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        } catch(e) {}
        
        // 2. Fix plugins (make it look populated)
        try {
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });
        } catch(e) {}
        
        // 3. Fix languages (common detection point)
        try {
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
        } catch(e) {}
        
        // 4. Chrome property
        try {
            if (!window.navigator.chrome) {
                window.navigator.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            }
        } catch(e) {}
        
        // 5. Permissions query
        try {
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
        } catch(e) {}
        
        // 6. Fix iframe detection
        try {
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    return window;
                }
            });
        } catch(e) {}
        
        // 7. Mock hardware concurrency (common detection)
        try {
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true
            });
        } catch(e) {}
        
        // 8. Mock device memory
        try {
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true
            });
        } catch(e) {}
        
        // 9. API Interception for Stealth Bypass
        window.__interceptedData = window.__interceptedData || [];
        
        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const response = await originalFetch.apply(this, args);
            try {
                let url = '';
                if (typeof args[0] === 'string') url = args[0];
                else if (args[0] && typeof args[0].url === 'string') url = args[0].url;
                
                if (url.includes('/api/v1/mixed_people/search') || url.includes('/api/v1/mixed_companies/search')) {
                    const clone = response.clone();
                    clone.json().then(data => {
                        window.__interceptedData.push({ url, data });
                    }).catch(e => {});
                }
            } catch(e) {}
            return response;
        };
        
        // Intercept XMLHttpRequest
        const originalXhrOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            this._url = url;
            return originalXhrOpen.apply(this, arguments);
        };
        const originalXhrSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function() {
            this.addEventListener('load', function() {
                if (typeof this._url === 'string' && (this._url.includes('/api/v1/mixed_people/search') || this._url.includes('/api/v1/mixed_companies/search'))) {
                    try {
                        const data = JSON.parse(this.responseText);
                        window.__interceptedData.push({ url: this._url, data });
                    } catch(e) {}
                }
            });
            return originalXhrSend.apply(this, arguments);
        };
        
        console.log('🔒 Advanced stealth mode activated');
        """
        
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            log_message("✅ Advanced stealth JavaScript injected", 'DEBUG')
        except Exception as e:
            log_message(f"⚠️  Stealth injection warning: {e}", 'WARNING')
    
    def _human_like_mouse_movement(self, element):
        """Simulate human-like mouse movement to element"""
        try:
            actions = ActionChains(self.driver)
            # Move to element with a slight random offset
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            actions.move_to_element_with_offset(element, offset_x, offset_y)
            actions.perform()
            random_delay(0.1, 0.3)
        except Exception as e:
            log_message(f"Mouse movement failed: {e}", 'DEBUG')
    
    def _human_like_typing(self, element, text: str):
        """Type text with human-like patterns and delays"""
        element.clear()
        random_delay(0.2, 0.5)
        
        for i, char in enumerate(text):
            element.send_keys(char)
            
            # Variable typing speed - humans don't type at constant speed
            if i % 5 == 0:  # Occasional pause (thinking)
                random_delay(0.15, 0.35)
            else:
                random_delay(0.05, 0.12)
            
            # Random typo and correction (10% chance)
            if random.random() < 0.1 and i < len(text) - 1:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(wrong_char)
                random_delay(0.1, 0.2)
                element.send_keys('\b')  # Backspace
                random_delay(0.05, 0.15)
    
    def save_cookies(self, filename: str = '/tmp/apollo_cookies.json'):
        """Save cookies for future sessions"""
        try:
            cookies = self.driver.get_cookies()
            with open(filename, 'w') as f:
                json.dump(cookies, f)
            log_message(f"✅ Cookies saved to {filename}", 'INFO')
            return cookies
        except Exception as e:
            log_message(f"❌ Failed to save cookies: {e}", 'ERROR')
            return None
    
    def load_cookies(self, cookies: List[Dict] = None, filename: str = '/tmp/apollo_cookies.json'):
        """Load cookies from file or list. Handles browser-exported cookie format."""
        try:
            if not cookies:
                # Try to load from file
                try:
                    with open(filename, 'r') as f:
                        cookies = json.load(f)
                    log_message(f"✅ Cookies loaded from {filename}", 'INFO')
                except FileNotFoundError:
                    log_message(f"⚠️  Cookie file not found: {filename}", 'WARNING')
                    return False
            
            if cookies:
                # Navigate to base domain first (required for setting cookies)
                # Using apollo.io covers both .apollo.io and app.apollo.io cookie domains
                self.driver.get("https://app.apollo.io/#/login")
                random_delay(2, 3)
                
                # Normalize and add cookies
                added = 0
                for cookie in cookies:
                    try:
                        # Normalize browser-exported cookie format to Selenium format
                        normalized = self._normalize_cookie(cookie)
                        if normalized:
                            self.driver.add_cookie(normalized)
                            added += 1
                    except Exception as e:
                        log_message(f"⚠️  Failed to add cookie '{cookie.get('name', '?')}': {e}", 'DEBUG')
                
                log_message(f"✅ Loaded {added}/{len(cookies)} cookies successfully!", 'SUCCESS')
                
                # Navigate to dashboard to verify cookies work
                # If cookies are valid, we'll land on the dashboard
                # If invalid, Apollo will redirect to /login
                self.driver.get("https://app.apollo.io/#/people")
                random_delay(3, 5)
                
                # Check if cookies worked (are we logged in?)
                if self._is_logged_in():
                    log_message("🎉 Cookie authentication successful! Skipping login.", 'SUCCESS')
                    self.logged_in = True
                    return True
                else:
                    log_message("⚠️  Cookies loaded but not logged in", 'WARNING')
                    return False
            
            return False
            
        except Exception as e:
            log_message(f"❌ Failed to load cookies: {e}", 'ERROR')
            return False
    
    def _normalize_cookie(self, cookie: Dict) -> Optional[Dict]:
        """
        Normalize a browser-exported cookie to Selenium-compatible format.
        
        Handles differences between browser cookie exports (EditThisCookie, DevTools)
        and what Selenium's add_cookie() expects.
        """
        normalized = {}
        
        # Required fields
        name = cookie.get('name')
        value = cookie.get('value')
        if not name or value is None:
            return None
        
        normalized['name'] = name
        normalized['value'] = str(value)
        
        # Domain
        if 'domain' in cookie:
            normalized['domain'] = cookie['domain']
        
        # Path
        normalized['path'] = cookie.get('path', '/')
        
        # Secure
        normalized['secure'] = cookie.get('secure', False)
        
        # HttpOnly
        normalized['httpOnly'] = cookie.get('httpOnly', False)
        
        # Expiry: browser exports use 'expirationDate', Selenium uses 'expiry'
        expiry = cookie.get('expiry') or cookie.get('expirationDate')
        if expiry:
            try:
                normalized['expiry'] = int(float(expiry))
            except (ValueError, TypeError):
                pass  # Skip invalid expiry, cookie will be session-only
        
        # SameSite: normalize browser format to Selenium format
        same_site = cookie.get('sameSite')
        if same_site:
            same_site_str = str(same_site).lower()
            if same_site_str in ('no_restriction', 'none', 'unspecified'):
                normalized['sameSite'] = 'None'
            elif same_site_str == 'lax':
                normalized['sameSite'] = 'Lax'
            elif same_site_str == 'strict':
                normalized['sameSite'] = 'Strict'
            # Skip null/invalid values — Selenium doesn't need sameSite
        
        return normalized
    
    def login(self, email: str = None, password: str = None, cookies: List[Dict] = None):
        """
        Login to Apollo.io account with cookie support.
        
        Args:
            email: Apollo email
            password: Apollo password
            cookies: Pre-saved cookies to skip login (RECOMMENDED)
        
        Returns:
            True if login successful
        """
        if not self.driver:
            self.setup_driver()
        
        # BEST PRACTICE: Try cookie-based authentication first
        if cookies:
            log_message("🔑 Attempting cookie-based authentication...", 'INFO')
            if self.load_cookies(cookies=cookies):
                return True
            else:
                log_message("⚠️  Cookie auth failed, falling back to password login", 'WARNING')
        
        # Fallback to password-based login
        if not email or not password:
            log_message("❌ Email and password are required for login", 'ERROR')
            return False
        
        log_message(f"🔐 Logging in as {email}...", 'INFO')
        
        try:
            # Navigate to login page
            self.driver.get(Config.APOLLO_LOGIN_URL)
            
            # Wait for page to load with human-like delay
            log_message("⏳ Waiting for login page to load...", 'INFO')
            random_delay(3, 5)
            
            # Random mouse movements (humans move mouse around)
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                for _ in range(random.randint(1, 3)):
                    self._human_like_mouse_movement(body)
            except:
                pass
            
            # Debug logging
            try:
                self.driver.save_screenshot('/tmp/login_page.png')
                log_message(f"📸 Screenshot saved. Page title: {self.driver.title}", 'INFO')
                log_message(f"🌐 Current URL: {self.driver.current_url}", 'INFO')
                
                all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                log_message(f"🔍 Found {len(all_inputs)} input fields", 'INFO')
            except Exception as debug_e:
                log_message(f"Debug failed: {debug_e}", 'WARNING')
            
            # Check for CAPTCHA before attempting login
            if self._check_for_captcha():
                log_message("❌ CAPTCHA detected on login page! Use cookie authentication instead.", 'ERROR')
                return False
            
            # Wait for email field with multiple selectors
            log_message("🔍 Looking for email field...", 'INFO')
            email_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "input[name='email'], input[type='email'], input[id*='email'], input[placeholder*='mail' i], input[aria-label*='email' i]"
                ))
            )
            
            # Human-like interaction with email field
            self._human_like_mouse_movement(email_field)
            random_delay(0.3, 0.7)
            self._human_like_typing(email_field, email)
            random_delay(0.5, 1.0)
            
            # Find and fill password field
            log_message("🔍 Looking for password field...", 'INFO')
            password_field = self.driver.find_element(
                By.CSS_SELECTOR, 
                "input[name='password'], input[type='password']"
            )
            
            self._human_like_mouse_movement(password_field)
            random_delay(0.3, 0.7)
            self._human_like_typing(password_field, password)
            random_delay(0.8, 1.5)
            
            # Random mouse movement before clicking submit
            try:
                self._human_like_mouse_movement(password_field)
            except:
                pass
            
            # Find and click login button
            log_message("🔍 Looking for login button...", 'INFO')
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except:
                login_button = self.driver.find_element(
                    By.XPATH, 
                    "//button[contains(text(), 'Sign in') or contains(text(), 'Log in') or contains(text(), 'sign in') or contains(text(), 'log in')]"
                )
            
            self._human_like_mouse_movement(login_button)
            random_delay(0.3, 0.6)
            login_button.click()
            
            log_message("✉️  Login form submitted, waiting for response...", 'INFO')
            random_delay(5, 8)
            
            # Check for CAPTCHA after submission
            if self._check_for_captcha():
                log_message("❌ CAPTCHA detected after login! Apollo has flagged this session.", 'ERROR')
                log_message("💡 SOLUTION: Use cookie-based authentication instead!", 'INFO')
                return False
            
            # Verify login success
            if self._is_logged_in():
                log_message("🎉 Login successful!", 'SUCCESS')
                self.logged_in = True
                
                # Save cookies for future use
                self.save_cookies()
                log_message("💡 TIP: Use saved cookies next time to skip login!", 'INFO')
                
                return True
            else:
                # Check for error messages
                try:
                    error_elem = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                    if error_elem:
                        error_text = error_elem[0].text
                        log_message(f"❌ Login failed: {error_text}", 'ERROR')
                    else:
                        log_message("❌ Login failed: Unknown error", 'ERROR')
                except:
                    log_message("❌ Login failed: Could not verify login status", 'ERROR')
                
                return False
                
        except TimeoutException:
            log_message("❌ Login form not found - page structure changed or blocked", 'ERROR')
            self.driver.save_screenshot('/tmp/timeout_error.png')
            return False
        except Exception as e:
            log_message(f"❌ Login error: {str(e)}", 'ERROR')
            try:
                self.driver.save_screenshot('/tmp/login_error.png')
            except:
                pass
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if currently logged into Apollo using multiple signals"""
        # Check 1: URL-based detection — if Apollo didn't redirect us to login, we're in
        try:
            current_url = self.driver.current_url.lower()
            if 'app.apollo.io' in current_url and '/login' not in current_url and '/signup' not in current_url:
                log_message(f"✅ URL indicates logged in: {current_url}", 'DEBUG')
                return True
        except Exception as e:
            log_message(f"URL check failed: {e}", 'DEBUG')
        
        # Check 2: DOM elements specific to logged-in Apollo UI
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "[data-cy='nav-home'], [class*='sidebar'], [class*='dashboard'], nav[class*='app'], [class*='avatar']"
                ))
            )
            return True
        except:
            pass
        
        # Check 3: Auth cookies — fallback signal
        try:
            driver_cookies = self.driver.get_cookies()
            cookie_names = {c['name'] for c in driver_cookies}
            auth_cookies = {'_leadgenie_session', 'remember_token_leadgenie_v2'}
            if auth_cookies & cookie_names:
                log_message(f"✅ Found auth cookies: {auth_cookies & cookie_names}", 'DEBUG')
                return True
        except Exception as e:
            log_message(f"Cookie check failed: {e}", 'DEBUG')
        
        log_message(f"Not logged in. Current URL: {self.driver.current_url}", 'DEBUG')
        return False
    
    def _check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present on page"""
        captcha_indicators = [
            "recaptcha", "captcha", "hcaptcha", "challenge", "cf-challenge"
        ]
        page_source = self.driver.page_source.lower()
        detected = any(indicator in page_source for indicator in captcha_indicators)
        
        if detected:
            log_message("⚠️  CAPTCHA detected on page!", 'WARNING')
            try:
                self.driver.save_screenshot('/tmp/captcha_detected.png')
                log_message("📸 CAPTCHA screenshot saved to /tmp/captcha_detected.png", 'INFO')
            except:
                pass
        
        return detected
    
    # ═══════════════════════════════════════════════════════════════
    # API-BASED SEARCH (PRIMARY) — Uses Apollo's internal API
    # ═══════════════════════════════════════════════════════════════
    
    def scrape_url(self, url: str, follow_links: bool = True, max_pages: int = None, min_delay: int = 3, max_delay: int = 7) -> List[Dict[str, Any]]:
        """
        Scrape data from a given Apollo.io URL.
        
        For search URLs (#/people, #/companies), uses Apollo's internal API
        to get structured JSON data with all fields.
        
        Args:
            url: Apollo.io URL to scrape
            follow_links: Not used in API mode (data is already complete)
            max_pages: Maximum number of pages to scrape
            min_delay: Minimum delay between API calls
            max_delay: Maximum delay between API calls
        
        Returns:
            List of extracted data dictionaries
        """
        if not is_valid_url(url):
            log_message(f"❌ Invalid Apollo.io URL: {url}", 'ERROR')
            return []
        
        if not self.logged_in:
            log_message("❌ Not logged in! Please login first.", 'ERROR')
            return []
        
        # Detect page type from URL (not HTML — Apollo is a SPA)
        page_type = detect_page_type(url=url)
        log_message(f"📄 Detected page type: {page_type}", 'INFO')
        
        # API-based extraction for search pages
        if page_type in ('people_search', 'company_search'):
            return self._scrape_search_via_api(
                url=url,
                search_type='people' if page_type == 'people_search' else 'organizations',
                max_pages=max_pages or Config.MAX_PAGES,
                min_delay=min_delay,
                max_delay=max_delay
            )
        
        # Fallback to HTML for profile pages
        log_message(f"🌐 Navigating to: {url}", 'INFO')
        self.driver.get(url)
        random_delay(min_delay, max_delay)
        
        if page_type == 'contact_profile':
            return [self._scrape_contact_profile()]
        elif page_type == 'company_profile':
            return [self._scrape_company_profile()]
        else:
            log_message("⚠️  Unknown page type, attempting generic extraction...", 'WARNING')
            return [self._scrape_generic_page()]
    
    def _build_search_url(self, filters: Dict, page: int = 1) -> str:
        """Build Apollo URL from filter parameters to trigger the API request."""
        import urllib.parse
        
        base_url = "https://app.apollo.io/#/people?"
        params = []
        
        if 'person_locations' in filters:
            for loc in filters['person_locations']:
                params.append(f"personLocations[]={urllib.parse.quote(loc)}")
                
        if 'person_titles' in filters:
            for t in filters['person_titles']:
                params.append(f"personTitles[]={urllib.parse.quote(t)}")
                
        if 'person_seniorities' in filters:
            for s in filters['person_seniorities']:
                params.append(f"personSeniorities[]={urllib.parse.quote(s)}")
                
        if 'organization_industries' in filters:
            for ind in filters['organization_industries']:
                params.append(f"organizationIndustries[]={urllib.parse.quote(ind)}")
                
        if 'organization_num_employees_ranges' in filters:
            for r in filters['organization_num_employees_ranges']:
                params.append(f"organizationNumEmployeesRanges[]={urllib.parse.quote(r)}")
        
        params.append(f"page={page}")
        params.append("sortByField=[none]")
        params.append("sortAscending=false")
        
        return base_url + "&".join(params)

    def _scrape_search_via_api(self, url: str, search_type: str = 'people', max_pages: int = 10, min_delay: int = 3, max_delay: int = 7) -> List[Dict[str, Any]]:
        """
        Scrape search results using network interception (Stealth Bypass).
        
        Instead of calling the API ourselves (which gets 422 Bot Detected),
        we navigate to the URL and let Apollo's frontend make the request.
        Our injected JS intercepts the response flawlessly.
        """
        all_results = []
        
        # Parse search URL into API filters
        parsed = parse_apollo_search_url(url)
        filters = parsed['filters']
        start_page = parsed.get('page', 1)
        
        for page_offset in range(max_pages):
            current_page = start_page + page_offset
            log_message(f"📄 Scraping page {current_page} via API Interception...", 'INFO')
            
            search_url = self._build_search_url(filters, current_page)
            
            # Clear previous intercepted data
            self.driver.execute_script("window.__interceptedData = [];")
            
            # Navigate to trigger the React app to fetch data
            log_message(f"🌐 Navigating to trigger API request...", 'DEBUG')
            self.driver.get(search_url)
            
            # Force refresh on first page of segment to guarantee React Router processes the new URL
            if page_offset == 0:
                random_delay(1, 2)
                self.driver.refresh()
                log_message("🔄 Refreshed page to ensure React app loads new filters.", 'DEBUG')
            
            # Wait for data to be intercepted
            api_response = None
            for _ in range(30):  # Wait up to 30 seconds
                random_delay(1, 1)
                
                # Check for intercepted data
                intercepted = self.driver.execute_script("return window.__interceptedData;")
                if intercepted and len(intercepted) > 0:
                    api_response = intercepted[-1].get('data')
                    break
                    
            if not api_response:
                log_message(f"⚠️  No API response intercepted for page {current_page}, stopping.", 'WARNING')
                break
                
            # Check for API errors in the response body
            if api_response.get('error'):
                log_message(f"❌ Apollo API returned error: {api_response['error']}", 'ERROR')
                break
            
            # Get pagination info
            pagination = get_pagination_info(api_response)
            total = pagination['total_entries']
            total_pages = pagination['total_pages']
            
            if page_offset == 0:
                log_message(f"📊 Total results available: {total} across {total_pages} pages", 'INFO')
                max_pages = min(max_pages, total_pages)
            
            # Flatten the results into structured records
            records = flatten_api_response(api_response, search_type)
            
            if not records:
                log_message(f"⚠️  No records on page {current_page}, stopping.", 'WARNING')
                break
            
            all_results.extend(records)
            log_message(f"✅ Page {current_page}: {len(records)} records (total so far: {len(all_results)})", 'SUCCESS')
            
            # Check if we've reached the last page
            if current_page >= total_pages:
                log_message(f"📄 Reached last page ({total_pages})", 'INFO')
                break
            
            # Human-like delay and scroll
            random_delay(min_delay, max_delay)
            try:
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(200, 600)});")
            except:
                pass
        
        log_message(f"🎉 Total records scraped: {len(all_results)}", 'SUCCESS')
        return all_results
    
    # ═══════════════════════════════════════════════════════════════
    # HTML FALLBACK — For profile pages and unknown page types
    # ═══════════════════════════════════════════════════════════════
    
    def _scrape_contact_profile(self) -> Dict[str, Any]:
        """Scrape current page as contact profile (HTML fallback)"""
        page_html = self.driver.page_source
        return parse_contact_profile(page_html)
    
    def _scrape_company_profile(self) -> Dict[str, Any]:
        """Scrape current page as company profile (HTML fallback)"""
        page_html = self.driver.page_source
        return parse_company_profile(page_html)
    
    def _scrape_generic_page(self) -> Dict[str, Any]:
        """Generic scraping for unknown page types"""
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        
        return {
            'type': 'generic',
            'url': self.driver.current_url,
            'title': self.driver.title,
            'text_content': soup.get_text()[:1000],
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """Close the browser and cleanup"""
        if self.driver:
            log_message("🔒 Closing browser...", 'INFO')
            try:
                self.driver.quit()
                log_message("✅ Browser closed successfully", 'SUCCESS')
            except Exception as e:
                log_message(f"⚠️  Error closing browser: {e}", 'WARNING')
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
