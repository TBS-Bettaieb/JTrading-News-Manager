"""
Economic calendar scraper for ForexFactory using Selenium WebDriver
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import re
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ForexFactoryScraper:
    """Scraper for ForexFactory economic calendar using Selenium"""
    
    def __init__(self, base_url: str = "https://www.forexfactory.com/calendar", 
                 timeout: int = 30, retry_attempts: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.driver = None
        self.wait = None
        self._driver_session_lost = False
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with stealth options"""
        try:
            logger.info("Setting up Chrome WebDriver...")
            
            chrome_options = Options()
            
            # Add stealth options to avoid detection and human verification
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Additional anti-detection options
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-field-trial-config')
            chrome_options.add_argument('--disable-back-forward-cache')
            
            # Randomize user agent with more realistic options
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ]
            selected_ua = random.choice(user_agents)
            chrome_options.add_argument(f'--user-agent={selected_ua}')
            
            # Window size randomization
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            # Additional options for better stealth and performance
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Temporarily disable headless mode for better JavaScript execution
            # chrome_options.add_argument('--headless')  # Run in headless mode for better performance
            
            logger.info("Downloading/updating ChromeDriver...")
            # Setup service and driver
            service = Service(ChromeDriverManager().install())
            logger.info("Starting Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute multiple scripts to hide automation indicators and avoid detection
            stealth_scripts = [
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
                "window.chrome = { runtime: {} }",
                "Object.defineProperty(navigator, 'permissions', {get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })})"
            ]
            
            for script in stealth_scripts:
                try:
                    self.driver.execute_script(script)
                except Exception as e:
                    logger.debug(f"Could not execute stealth script: {e}")
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.timeout)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except ImportError as e:
            logger.error(f"Selenium import error: {e}")
            logger.error("Please ensure Selenium is installed: pip install selenium webdriver-manager")
            raise
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            logger.error("Make sure Chrome browser is installed on your system")
            logger.error("You can download Chrome from: https://www.google.com/chrome/")
            raise
    
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def _simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection"""
        try:
            if not self.driver:
                return
            
            # Longer, more realistic human behavior simulation
            # Random scroll to simulate reading with longer delays
            scroll_script = f"window.scrollTo(0, {random.randint(100, 500)})"
            self.driver.execute_script(scroll_script)
            time.sleep(random.uniform(2.0, 5.0))  # Longer reading simulation
            
            # Additional reading pause
            time.sleep(random.uniform(1.0, 3.0))
            
            # Random mouse move simulation with longer delays
            try:
                action = ActionChains(self.driver)
                action.move_by_offset(random.randint(50, 200), random.randint(50, 200)).perform()
                time.sleep(random.uniform(1.0, 3.0))  # Longer mouse pause
            except Exception:
                # If ActionChains fails, continue without it
                pass
            
            # Final pause to simulate human thinking/reading
            time.sleep(random.uniform(2.0, 4.0))
                
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {e}")
    
    def _navigate_to_page(self, url: str) -> bool:
        """Navigate to a page with retry logic and error handling"""
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Navigating to: {url} (attempt {attempt + 1})")
                
                # Add significant delay before navigation to avoid triggering verification
                if attempt > 0:
                    delay = random.uniform(10.0, 20.0)  # Much longer delay between retries
                    logger.debug(f"Waiting {delay:.1f} seconds before retry (longer delay to avoid verification)...")
                    time.sleep(delay)
                else:
                    # Even on first attempt, add a small delay
                    initial_delay = random.uniform(3.0, 8.0)
                    logger.debug(f"Initial navigation delay: {initial_delay:.1f}s")
                    time.sleep(initial_delay)
                
                # Navigate to the page
                self.driver.get(url)
                
                # Simulate human-like behavior after navigation
                self._simulate_human_behavior()
                
                # Wait significantly longer for page to load, especially for verification pages
                initial_wait = random.uniform(8.0, 15.0)
                logger.debug(f"Initial page load wait: {initial_wait:.1f}s")
                time.sleep(initial_wait)
                
                # Check for human verification page and error pages
                if self._is_human_verification_page():
                    logger.warning(f"Hit human verification page for {url}. Waiting for automatic resolution...")
                    
                    # Wait SIGNIFICANTLY longer for verification to complete automatically
                    max_verification_wait = 180  # Wait up to 3 minutes (180 seconds)
                    verification_check_interval = 10  # Check every 10 seconds instead of 5
                    
                    logger.info(f"Starting verification wait: up to {max_verification_wait}s with {verification_check_interval}s intervals...")
                    
                    for verification_attempt in range(max_verification_wait // verification_check_interval):
                        logger.debug(f"Verification wait attempt {verification_attempt + 1}: waiting {verification_check_interval}s...")
                        time.sleep(verification_check_interval)
                        
                        # Check if verification has completed and session is still valid
                        if not self._is_human_verification_page():
                            total_wait_time = verification_attempt * verification_check_interval
                            logger.info(f"Human verification completed automatically after {total_wait_time}s")
                            
                            # Add extra wait after verification completes to ensure page is fully loaded
                            logger.debug("Adding extra 15s wait after verification completion...")
                            time.sleep(15)
                            
                            # Check if driver session is still valid after verification
                            if not self._is_driver_responsive():
                                logger.warning("Driver session became invalid after verification. Need to reinitialize.")
                                if self._handle_invalid_session():
                                    logger.info("Driver reinitialized. Continuing with navigation retry.")
                                    # Break out of verification loop and let the navigation retry
                                    break
                                else:
                                    logger.error("Failed to reinitialize driver. Giving up on this URL.")
                                    return False
                            break
                    else:
                        logger.warning(f"Verification page did not resolve after {max_verification_wait}s. Trying refresh and extended wait...")
                        # Try to refresh and wait much longer
                        try:
                            self.driver.refresh()
                            logger.info("Page refreshed. Waiting additional 60s...")
                            time.sleep(60)  # Wait a full minute after refresh
                            
                            # Check again if verification completed
                            if not self._is_human_verification_page():
                                logger.info("Verification completed after refresh and extended wait")
                            else:
                                logger.warning("Verification still present after refresh and extended wait")
                        except Exception as refresh_error:
                            logger.error(f"Error during refresh: {refresh_error}")
                    
                    # Check if driver session is still valid after handling verification
                    if not self._is_driver_responsive():
                        logger.warning("Driver session lost after verification handling. Reinitializing...")
                        if not self._handle_invalid_session():
                            logger.error("Failed to reinitialize driver after verification. Skipping this URL.")
                            return False
                    
                    continue
                
                if "404" in self.driver.title or "403" in self.driver.page_source:
                    logger.warning(f"Got error page for {url}")
                    continue
                
                # Add an additional wait and check for verification page that might appear later
                logger.debug("Waiting additional 20s and checking again for verification page...")
                time.sleep(20)
                
                # Double-check for verification page that might have appeared
                if self._is_human_verification_page():
                    logger.warning(f"Detected verification page on delayed check for {url}. Handling...")
                    # Use the same verification handling logic as above
                    max_verification_wait = 120  # Shorter wait for delayed detection
                    verification_check_interval = 10
                    
                    for verification_attempt in range(max_verification_wait // verification_check_interval):
                        logger.debug(f"Delayed verification check {verification_attempt + 1}: waiting {verification_check_interval}s...")
                        time.sleep(verification_check_interval)
                        
                        if not self._is_human_verification_page():
                            logger.info(f"Delayed verification completed after {verification_attempt * verification_check_interval + 20}s")
                            break
                    else:
                        logger.warning("Delayed verification did not complete. Continuing with page...")
                
                logger.debug(f"Successfully loaded page: {self.driver.title}")
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout loading {url} on attempt {attempt + 1}")
            except WebDriverException as e:
                error_msg = str(e).lower()
                logger.warning(f"WebDriver error loading {url}: {e}")
                
                # Check if this is an invalid session error
                if "invalid session id" in error_msg or "session deleted" in error_msg:
                    logger.warning("Detected invalid session during navigation. Attempting to reinitialize driver...")
                    if self._handle_invalid_session():
                        # Continue with the same attempt since we have a new driver
                        continue
                    else:
                        logger.error("Failed to reinitialize driver. Skipping this URL.")
                        return False
            except Exception as e:
                logger.warning(f"Unexpected error loading {url}: {e}")
                
            if attempt < self.retry_attempts - 1:
                # Significantly longer delay between retries to avoid triggering more verification
                delay = random.uniform(15.0, 30.0)
                logger.debug(f"Waiting {delay:.1f} seconds before retry to avoid triggering verification...")
                time.sleep(delay)
        
        logger.error(f"Failed to load {url} after {self.retry_attempts} attempts")
        return False
    
    def _is_human_verification_page(self) -> bool:
        """Check if the current page is a human verification page"""
        try:
            if not self.driver:
                return False
            
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()
            
            # Check for common human verification indicators
            verification_indicators = [
                "nous vérifions que vous êtes humain",
                "we are verifying you are human",
                "please wait while your request is being verified",
                "checking your browser",
                "security check",
                "verifying your connection",
                "human verification",
                "cloudflare",
                "ddos protection",
                "cette opération peut prendre quelques secondes",  # Exact text from your example
                "doit vérifier la sécurité de votre connexion"  # Exact text from your example
            ]
            
            for indicator in verification_indicators:
                if indicator in page_source or indicator in page_title:
                    logger.debug(f"Found verification indicator: '{indicator}'")
                    return True
            
            # Check for specific ForexFactory verification text (French)
            if "www.forexfactory.com doit vérifier" in page_source:
                logger.debug("Found ForexFactory verification page")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking for verification page: {e}")
            return False
    
    def _is_weekend(self, date: datetime) -> bool:
        """Check if the given date is a weekend (Saturday or Sunday)"""
        # Python weekday(): Monday = 0, Sunday = 6
        # Saturday = 5, Sunday = 6
        return date.weekday() in [5, 6]
    
    def _should_skip_date(self, date: datetime) -> bool:
        """Determine if a date should be skipped (weekends typically have no economic events)"""
        return self._is_weekend(date)
    
    def scrape_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Scrape economic events for a date range, skipping weekends"""
        events = []
        
        try:
            # Calculate total days and estimate weekends in range
            total_days = (end_date - start_date).days + 1
            estimated_weekends = total_days // 7 * 2  # Rough estimate
            
            logger.info(f"Starting scrape from {start_date.date()} to {end_date.date()}")
            logger.info(f"Total days in range: {total_days}, estimated weekend days to skip: ~{estimated_weekends}")
            
            current_date = start_date
            is_first_request = True
            weekends_skipped = 0
            failed_days = 0
            successful_days = 0
            
            while current_date <= end_date:
                # Skip weekends (no economic events typically on weekends)
                if self._should_skip_date(current_date):
                    logger.debug(f"Skipping {current_date.strftime('%A, %Y-%m-%d')} (weekend)")
                    weekends_skipped += 1
                    current_date += timedelta(days=1)
                    continue
                
                # Scrape the day if it's a weekday with retry logic
                day_events = self._scrape_day_with_retry(current_date, is_first_request)
                if day_events is not None:  # None means complete failure after retries
                    events.extend(day_events)
                    successful_days += 1
                    # Close driver after each successful scrape to avoid Cloudflare detection
                    logger.debug("Closing driver after successful scrape to start fresh session for next page")
                    self._close_driver()
                else:
                    failed_days += 1
                is_first_request = False
                
                current_date += timedelta(days=1)
                
                # Random delay between days (shorter since we skip weekends)
                delay = random.uniform(2.0, 5.0)
                logger.debug(f"Waiting {delay:.1f} seconds before next day...")
                time.sleep(delay)
            
            # Calculate efficiency metrics
            total_weekdays = total_days - weekends_skipped
            efficiency_percent = (weekends_skipped / total_days * 100) if total_days > 0 else 0
            success_rate = (successful_days / total_weekdays * 100) if total_weekdays > 0 else 0
            
            logger.info("=" * 60)
            logger.info("SCRAPING COMPLETED - SUMMARY REPORT")
            logger.info("=" * 60)
            logger.info(f"[TOTAL] Total events found: {len(events)}")
            logger.info(f"[RANGE] Date range: {start_date.date()} to {end_date.date()}")
            logger.info(f"[DAYS] Total days in range: {total_days}")
            logger.info(f"[SKIPPED] Weekend days skipped: {weekends_skipped}/{total_days} ({efficiency_percent:.1f}%)")
            logger.info(f"[SUCCESS] Successful weekdays: {successful_days}/{total_weekdays} ({success_rate:.1f}%)")
            logger.info(f"[FAILED] Failed days: {failed_days}")
            logger.info(f"[OPTIMIZATION] Efficiency gain: {efficiency_percent:.1f}% fewer requests (weekend optimization)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            self._close_driver()
        
        return events
    
    def _scrape_day_with_retry(self, target_date: datetime, first_request: bool = False) -> Optional[List[Dict]]:
        """Scrape events for a specific day with retry logic and better error handling"""
        date_str = target_date.strftime("%b%d.%Y").lower()
        max_attempts = 3
        
        # Initialize driver if not present (needed after browser restart strategy)
        if not self.driver:
            logger.debug(f"Driver not initialized for {date_str}, setting up fresh driver")
            self._setup_driver()
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Attempting to scrape {date_str} (attempt {attempt + 1}/{max_attempts})")
                
                day_events = self._scrape_day(target_date, first_request and attempt == 0)
                
                if day_events is not None:
                    if len(day_events) > 0:
                        logger.debug(f"Successfully scraped {len(day_events)} events for {date_str}")
                    else:
                        logger.debug(f"No events found for {date_str} (may be normal for some days)")
                    return day_events
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Attempt {attempt + 1} failed for {date_str}: {e}")
                
                # Check if this is an invalid session error
                if "invalid session id" in error_msg or "session deleted" in error_msg or hasattr(self, '_driver_session_lost') and self._driver_session_lost:
                    logger.warning("Detected invalid session during scraping. Attempting to reinitialize driver...")
                    if self._handle_invalid_session():
                        logger.info("Driver reinitialized. Continuing scrape attempt.")
                        # Reset the flag and continue with the same attempt
                        self._driver_session_lost = False
                        continue
                    else:
                        logger.error("Failed to reinitialize driver. Skipping this date.")
                        return None
                
                if attempt < max_attempts - 1:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(1.0, 3.0)
                    logger.debug(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed for {date_str}")
                    return None
        
        return None
    
    def _scrape_day(self, target_date: datetime, first_request: bool = False) -> List[Dict]:
        """Scrape events for a specific day using JavaScript calendarComponentStates"""
        # ForexFactory uses format: mar5.2025, apr11.2025
        month_abbr = target_date.strftime("%b").lower()
        day = target_date.day
        year = target_date.year
        date_str = f"{month_abbr}{day}.{year}"
        url = f"{self.base_url}?day={date_str}"
        
        logger.debug(f"Scraping day: {target_date.date()} - URL: {url}")
        
        # Navigate to the page
        if not self._navigate_to_page(url):
            return []
        
        events = []
        
        try:
            # Wait for page to load and JavaScript to execute
            time.sleep(random.uniform(2.0, 4.0))
            
            # Check if driver is still responsive after navigation and wait
            if not self._is_driver_responsive():
                logger.error(f"WebDriver became unresponsive after navigation for {date_str}")
                return []
            
            # Extract calendarComponentStates from JavaScript
            calendar_data = self._extract_calendar_data_from_js(target_date)
            
            if calendar_data:
                events = self._parse_js_calendar_data(calendar_data, target_date)
                logger.info(f"Scraped {len(events)} events for {date_str} using JS data")
                
                # Enhance JS events with HTML data for Actual/Forecast/Previous values
                events = self._enhance_js_events_with_html_data(events, target_date)
                
            else:
                logger.warning(f"No calendar data found in JavaScript for {date_str}, falling back to HTML parsing")
                # Fallback to original HTML parsing if JS extraction fails
                events = self._scrape_day_fallback_html(target_date, date_str)
                    
        except Exception as e:
            logger.error(f"Error parsing calendar for {date_str}: {e}")
            logger.info("Falling back to HTML parsing...")
            events = self._scrape_day_fallback_html(target_date, date_str)
        
        return events
    
    def _extract_calendar_data_from_js(self, target_date: datetime) -> Optional[Dict]:
        """Extract calendarComponentStates data from JavaScript"""
        try:
            # Wait longer for JavaScript to load and execute
            max_wait_time = 10
            wait_interval = 1
            
            for attempt in range(max_wait_time):
                # Enhanced JavaScript to extract calendarComponentStates with better debugging
                js_script = """
                var result = {
                    calendarStates: null,
                    pageData: null,
                    debug: {
                        windowObject: null,
                        calendarComponentStatesExists: false,
                        calendarComponentStatesType: null,
                        calendarComponentStatesKeys: null
                    }
                };
                
                // Debug: Check window object
                result.debug.windowObject = (typeof window !== 'undefined');
                
                // Extract calendarComponentStates with detailed debugging
                try {
                    if (typeof window !== 'undefined' && window.calendarComponentStates !== undefined) {
                        result.debug.calendarComponentStatesExists = true;
                        result.debug.calendarComponentStatesType = typeof window.calendarComponentStates;
                        result.calendarStates = window.calendarComponentStates;
                        
                        if (window.calendarComponentStates && typeof window.calendarComponentStates === 'object') {
                            result.debug.calendarComponentStatesKeys = Object.keys(window.calendarComponentStates);
                        }
                    }
                } catch(e) {
                    result.debug.error = e.toString();
                }
                
                // Try to extract additional data from the page
                try {
                    if (typeof window.ffGlobal !== 'undefined') {
                        result.pageData = window.ffGlobal;
                    }
                } catch(e) {
                    // Ignore errors for additional data extraction
                }
                
                return result;
                """
                
                # Check if driver is still responsive before executing script
                if not self._is_driver_responsive():
                    logger.error(f"WebDriver not responsive during JS extraction attempt {attempt + 1}")
                    return None
                
                result = self.driver.execute_script(js_script)
                
                if result:
                    debug_info = result.get('debug', {})
                    logger.debug(f"JS extraction attempt {attempt + 1}: window={debug_info.get('windowObject')}, "
                               f"calendarComponentStates exists={debug_info.get('calendarComponentStatesExists')}, "
                               f"type={debug_info.get('calendarComponentStatesType')}")
                    
                    if result.get('calendarStates'):
                        logger.debug(f"Successfully extracted calendarComponentStates on attempt {attempt + 1}")
                        logger.debug(f"Calendar states keys: {debug_info.get('calendarComponentStatesKeys', [])}")
                        return result['calendarStates']
                
                if attempt < max_wait_time - 1:
                    logger.debug(f"calendarComponentStates not ready, waiting {wait_interval}s...")
                    time.sleep(wait_interval)
            
            # Final attempt with more detailed debugging
            final_debug_script = """
            return {
                windowDefined: typeof window !== 'undefined',
                calendarComponentStatesDefined: typeof window.calendarComponentStates !== 'undefined',
                calendarComponentStatesValue: window.calendarComponentStates,
                allGlobalVars: Object.keys(window).filter(k => k.includes('calendar') || k.includes('Calendar'))
            };
            """
            
            # Final debug attempt with driver check
            if not self._is_driver_responsive():
                logger.error("WebDriver not responsive for final debug attempt")
                return None
            
            final_debug = self.driver.execute_script(final_debug_script)
            logger.warning(f"Final JS debug info: {final_debug}")
            logger.warning("calendarComponentStates not found in JavaScript after all attempts")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting calendar data from JavaScript: {e}")
            return None
    
    def _parse_js_calendar_data(self, calendar_data: Dict, target_date: datetime) -> List[Dict]:
        """Parse calendar data from JavaScript calendarComponentStates"""
        events = []
        
        try:
            # Navigate through the calendarComponentStates structure
            for key, calendar_state in calendar_data.items():
                if isinstance(calendar_state, dict) and 'days' in calendar_state:
                    for day_data in calendar_state['days']:
                        if 'events' in day_data:
                            for event_data in day_data['events']:
                                event = self._parse_js_event_data(event_data, target_date)
                                if event:
                                    events.append(event)
        
        except Exception as e:
            logger.error(f"Error parsing JavaScript calendar data: {e}")
        
        return events
    
    def _parse_js_event_data(self, event_data: Dict, target_date: datetime) -> Optional[Dict]:
        """Parse individual event data from JavaScript structure"""
        try:
            # Convert timestamp to datetime if available
            event_time = target_date.replace(hour=12, minute=0)  # Default time
            if 'dateline' in event_data and event_data['dateline']:
                try:
                    event_time = datetime.fromtimestamp(event_data['dateline'])
                except:
                    pass
            
            # Extract basic information with better field mapping
            event_name = event_data.get('name', '')
            prefixed_name = event_data.get('prefixedName', event_name)
            trimmed_name = event_data.get('trimmedPrefixedName', prefixed_name)
            solo_title = event_data.get('soloTitle', trimmed_name)
            
            currency = event_data.get('currency', '')
            country_code = event_data.get('country', '')
            
            # Extract additional data if available
            notice = event_data.get('notice', '')
            has_data_values = event_data.get('hasDataValues', False)
            has_graph = event_data.get('hasGraph', False)
            has_linked_threads = event_data.get('hasLinkedThreads', False)
            
            # Log available fields for debugging
            available_fields = list(event_data.keys())
            logger.debug(f"JS Event data fields available: {available_fields}")
            
            # Try to extract impact level from available data or HTML
            impact = self._extract_impact_from_js_data(event_data)
            
            # For now, set placeholder values for Actual/Forecast/Previous
            # These would need to be extracted from the HTML table if not in JS
            actual = 'N/A'
            forecast = 'N/A' 
            previous = 'N/A'
            
            # Use the best available event name
            final_event_name = solo_title or trimmed_name or prefixed_name or event_name
            
            if final_event_name:  # Only return events that have a name
                return {
                    'DateTime': event_time,
                    'Event': final_event_name,
                    'Country': self._get_country_name_from_code(country_code),
                    'Impact': impact,
                    'Currency': currency,
                    'Actual': actual,
                    'Forecast': forecast,
                    'Previous': previous,
                    'Notice': notice if notice else '',
                    'HasDataValues': has_data_values,
                    'HasGraph': has_graph,
                    'HasLinkedThreads': has_linked_threads
                }
            else:
                logger.debug("Skipping event without name")
                return None
            
        except Exception as e:
            logger.error(f"Error parsing JS event data: {e}")
            return None
    
    def _extract_impact_from_js_data(self, event_data: Dict) -> str:
        """Try to extract impact level from JavaScript data"""
        # This is a placeholder - the impact level might be in the HTML or other JS variables
        # For now, return default, but we could enhance this based on ForexFactory's structure
        
        # Check if there are any clues in the event data
        if 'impact' in event_data:
            return str(event_data['impact']).title()
        
        # Check for other possible impact indicators
        event_id = event_data.get('id', 0)
        ebase_id = event_data.get('ebaseId', 0)
        
        # As a fallback, try to determine from the page HTML
        try:
            # This could be enhanced to look up impact from HTML based on event ID
            pass
        except:
            pass
            
        return 'Low'  # Default impact level
    
    def _get_country_name_from_code(self, country_code: str) -> str:
        """Convert country code to full country name"""
        country_mapping = {
            'US': 'United States',
            'EUR': 'Eurozone',
            'GB': 'United Kingdom',
            'UK': 'United Kingdom',
            'JP': 'Japan',
            'CH': 'Switzerland',
            'AU': 'Australia',
            'NZ': 'New Zealand',
            'CA': 'Canada',
            'CN': 'China',
            'FR': 'France',
            'DE': 'Germany',
            'IT': 'Italy',
            'ES': 'Spain',
            'RU': 'Russia',
            'BR': 'Brazil',
            'IN': 'India',
            'MX': 'Mexico',
            'ZA': 'South Africa'
        }
        
        return country_mapping.get(country_code.upper(), 'Unknown')
    
    def _enhance_js_events_with_html_data(self, js_events: List[Dict], target_date: datetime) -> List[Dict]:
        """Enhance JavaScript events with HTML data for Actual/Forecast/Previous values"""
        try:
            # Get HTML source and parse it
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the calendar table
            calendar_table = soup.find('table', class_='calendar__table')
            if not calendar_table:
                logger.debug("No calendar table found for HTML enhancement")
                return js_events
            
            # Find event rows
            tbody = calendar_table.find('tbody')
            if not tbody:
                logger.debug("No tbody found for HTML enhancement")
                return js_events
            
            rows = tbody.find_all('tr', class_='calendar__row')
            logger.debug(f"Found {len(rows)} HTML rows to enhance {len(js_events)} JS events")
            
            # Map JS events to HTML rows by event name matching
            for js_event in js_events:
                js_event_name = js_event.get('Event', '')
                
                # Try to find matching HTML row
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        # Get event name from HTML
                        event_cell = cells[3] if len(cells) > 3 else None
                        if event_cell:
                            event_link = event_cell.find('a')
                            html_event_name = event_link.get_text(strip=True) if event_link else event_cell.get_text(strip=True)
                            
                            # Try to match events (simple name matching)
                            if html_event_name and js_event_name and html_event_name.lower() in js_event_name.lower():
                                # Extract values from HTML cells
                                actual_cell = cells[4] if len(cells) > 4 else None
                                forecast_cell = cells[5] if len(cells) > 5 else None
                                previous_cell = cells[6] if len(cells) > 6 else None
                                
                                # Update JS event with HTML data
                                js_event['Actual'] = self._get_cell_text(actual_cell)
                                js_event['Forecast'] = self._get_cell_text(forecast_cell)
                                js_event['Previous'] = self._get_cell_text(previous_cell)
                                
                                # Also try to extract better impact from HTML
                                impact_cell = cells[2] if len(cells) > 2 else None
                                if impact_cell:
                                    html_impact = self._parse_impact_level(impact_cell)
                                    if html_impact != 'Low':  # Only update if we found a non-default impact
                                        js_event['Impact'] = html_impact
                                
                                logger.debug(f"Enhanced JS event '{js_event_name}' with HTML data")
                                break
            
        except Exception as e:
            logger.error(f"Error enhancing JS events with HTML data: {e}")
        
        return js_events
    
    def _scrape_day_fallback_html(self, target_date: datetime, date_str: str) -> List[Dict]:
        """Fallback method to scrape using HTML parsing if JavaScript extraction fails"""
        events = []
        
        try:
            # Check if driver is still responsive
            if not self._is_driver_responsive():
                logger.error(f"WebDriver not responsive for HTML fallback on {date_str}")
                return events
            
            # Wait for calendar table to load with better error handling
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'calendar__table')))
                logger.debug("Calendar table found for HTML fallback")
            except TimeoutException:
                logger.warning(f"Calendar table not found within timeout for {date_str}")
                return events
            except Exception as e:
                logger.error(f"Error waiting for calendar table: {e}")
                return events
            
            # Wait a bit more for dynamic content
            time.sleep(random.uniform(1.0, 2.0))
            
            # Check driver again before getting page source
            if not self._is_driver_responsive():
                logger.error(f"WebDriver became unresponsive while getting page source for {date_str}")
                return events
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            if not page_source or len(page_source.strip()) == 0:
                logger.warning(f"Empty page source for {date_str}")
                return events
                
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the calendar table
            calendar_table = soup.find('table', class_='calendar__table')
            if not calendar_table:
                logger.warning(f"No calendar table found for {date_str}")
                return events
            
            # Find event rows
            tbody = calendar_table.find('tbody')
            if not tbody:
                logger.warning(f"No tbody found for {date_str}")
                return events
            
            rows = tbody.find_all('tr', class_='calendar__row')
            logger.debug(f"Found {len(rows)} event rows for {date_str} (HTML fallback)")
            
            for row in rows:
                try:
                    event = self._parse_event_row(row, target_date)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing individual row for {date_str}: {e}")
                    continue
                    
        except WebDriverException as e:
            logger.error(f"WebDriver error in HTML fallback for {date_str}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in HTML fallback parsing for {date_str}: {e}")
        
        logger.info(f"HTML Fallback: Scraped {len(events)} events for {date_str}")
        return events
    
    def _is_driver_responsive(self) -> bool:
        """Check if the WebDriver is still responsive and session is valid"""
        try:
            if not self.driver:
                return False
            # Try a simple command to check if driver is responsive
            # This will throw an exception if session is invalid
            current_url = self.driver.current_url
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid session id" in error_msg or "session deleted" in error_msg:
                logger.warning(f"WebDriver session became invalid: {e}")
                self._driver_session_lost = True
                return False
            else:
                logger.debug(f"Driver not responsive: {e}")
                return False
    
    def _handle_invalid_session(self) -> bool:
        """Handle invalid WebDriver session by reinitializing the driver"""
        try:
            logger.warning("Detected invalid WebDriver session. Attempting to reinitialize...")
            
            # Close the invalid driver first
            self._close_driver()
            
            # Wait a moment before reinitializing
            time.sleep(random.uniform(2.0, 5.0))
            
            # Reinitialize the driver
            self._setup_driver()
            
            # Reset the session lost flag
            self._driver_session_lost = False
            
            logger.info("WebDriver successfully reinitialized after invalid session")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reinitialize WebDriver after invalid session: {e}")
            return False
    
    def _parse_event_row(self, row, target_date: datetime) -> Optional[Dict]:
        """Parse a single event row from the calendar"""
        try:
            cells = row.find_all('td')
            if len(cells) < 7:
                return None
            
            # Extract basic event information (adjust indices based on ForexFactory structure)
            time_cell = cells[0] if len(cells) > 0 else None
            currency_cell = cells[1] if len(cells) > 1 else None
            impact_cell = cells[2] if len(cells) > 2 else None
            event_cell = cells[3] if len(cells) > 3 else None
            actual_cell = cells[4] if len(cells) > 4 else None
            forecast_cell = cells[5] if len(cells) > 5 else None
            previous_cell = cells[6] if len(cells) > 6 else None
            
            # Parse time
            time_text = time_cell.get_text(strip=True) if time_cell else "All Day"
            if not time_text or time_text == 'All Day':
                event_time = target_date.replace(hour=0, minute=0)
            else:
                event_time = self._parse_time_string(time_text, target_date)
            
            # Parse currency
            currency = "USD"  # Default
            if currency_cell:
                currency_link = currency_cell.find('a')
                currency = currency_link.get_text(strip=True) if currency_link else currency_cell.get_text(strip=True)
            
            # Parse impact
            impact = self._parse_impact_level(impact_cell) if impact_cell else 'Low'
            
            # Parse event name
            event_name = ""
            if event_cell:
                event_link = event_cell.find('a')
                event_name = event_link.get_text(strip=True) if event_link else event_cell.get_text(strip=True)
            
            # Parse country
            country = self._extract_country_from_event(event_name, currency)
            
            # Parse values
            actual = self._get_cell_text(actual_cell)
            forecast = self._get_cell_text(forecast_cell)
            previous = self._get_cell_text(previous_cell)
            
            return {
                'DateTime': event_time,
                'Event': event_name,
                'Country': country,
                'Impact': impact,
                'Currency': currency,
                'Actual': actual,
                'Forecast': forecast,
                'Previous': previous
            }
            
        except Exception as e:
            logger.error(f"Error parsing event row: {e}")
            return None
    
    def _get_cell_text(self, cell) -> str:
        """Extract text from a table cell"""
        if not cell:
            return 'N/A'
        
        text = cell.get_text(strip=True)
        if not text or text == '-' or text == '':
            return 'N/A'
        return text
    
    def _parse_impact_level(self, impact_cell) -> str:
        """Parse impact level from impact cell"""
        if not impact_cell:
            return 'Low'
        
        # Look for impact indicators in class names or text
        cell_html = str(impact_cell)
        if 'high' in cell_html.lower():
            return 'High'
        elif 'medium' in cell_html.lower():
            return 'Medium'
        else:
            return 'Low'
    
    def _parse_time_string(self, time_str: str, target_date: datetime) -> datetime:
        """Parse time string and combine with target date"""
        try:
            # Handle various time formats
            if 'AM' in time_str or 'PM' in time_str:
                time_obj = datetime.strptime(time_str, "%I:%M%p").time()
            elif ':' in time_str:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
            else:
                return target_date.replace(hour=12, minute=0)
            
            return datetime.combine(target_date.date(), time_obj)
        except:
            return target_date.replace(hour=12, minute=0)
    
    def _extract_country_from_event(self, event_name: str, currency: str) -> str:
        """Extract country name from event or currency"""
        country_mapping = {
            'USD': 'United States',
            'EUR': 'Eurozone',
            'GBP': 'United Kingdom',
            'JPY': 'Japan',
            'CHF': 'Switzerland',
            'AUD': 'Australia',
            'NZD': 'New Zealand',
            'CAD': 'Canada',
            'CNY': 'China'
        }
        
        # Look for common country indicators in event name
        if 'US' in event_name or 'United States' in event_name:
            return 'United States'
        elif 'Euro' in event_name or 'European' in event_name:
            return 'Eurozone'
        elif 'UK' in event_name or 'British' in event_name:
            return 'United Kingdom'
        elif 'Japan' in event_name:
            return 'Japan'
        elif 'Swiss' in event_name:
            return 'Switzerland'
        elif 'Australian' in event_name:
            return 'Australia'
        elif 'New Zealand' in event_name:
            return 'New Zealand'
        elif 'Canadian' in event_name:
            return 'Canada'
        elif 'Chinese' in event_name:
            return 'China'
        
        # Fallback to currency mapping
        return country_mapping.get(currency, 'Unknown')