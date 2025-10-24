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
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Import CSV exporter and symbol mapper for immediate saving
from csv_exporter import CSVExporter
from symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)


class ForexFactoryScraper:
    """Scraper for ForexFactory economic calendar using Selenium"""
    
    def __init__(self, base_url: str = "https://www.forexfactory.com/calendar", 
                 timeout: int = 15, retry_attempts: int = 3, csv_exporter=None, symbol_mapper=None, headless: bool = True):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.headless = headless
        self.driver = None
        self.wait = None
        self._driver_session_lost = False
        self.csv_exporter = csv_exporter
        self.symbol_mapper = symbol_mapper or SymbolMapper()
        
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
            
            # Enable headless mode if requested
            if self.headless:
                chrome_options.add_argument('--headless')  # Run in headless mode for background operation
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                
            logger.info(f"Chrome WebDriver configured with headless mode: {self.headless}")
            
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
            # self.wait = WebDriverWait(self.driver, self.timeout)  # REMOVED - no WebDriverWait timeout
            
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
            # time.sleep(random.uniform(2.0, 5.0))  # Longer reading simulation - REMOVED
            
            # Additional reading pause
            # time.sleep(random.uniform(1.0, 3.0)) - REMOVED
            
            # Random mouse move simulation with longer delays
            try:
                action = ActionChains(self.driver)
                action.move_by_offset(random.randint(50, 200), random.randint(50, 200)).perform()
                # time.sleep(random.uniform(1.0, 3.0))  # Longer mouse pause - REMOVED
            except Exception:
                # If ActionChains fails, continue without it
                pass
            
            # Final pause to simulate human thinking/reading
            # time.sleep(random.uniform(2.0, 4.0)) - REMOVED
                
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
                    # time.sleep(delay) - REMOVED
                else:
                    # Even on first attempt, add a small delay
                    initial_delay = random.uniform(3.0, 8.0)
                    logger.debug(f"Initial navigation delay: {initial_delay:.1f}s")
                    # time.sleep(initial_delay) - REMOVED
                
                # Navigate to the page
                self.driver.get(url)
                
                # Simulate human-like behavior after navigation
                self._simulate_human_behavior()
                
                # Wait significantly longer for page to load, especially for verification pages
                initial_wait = random.uniform(8.0, 15.0)
                logger.debug(f"Initial page load wait: {initial_wait:.1f}s")
                # time.sleep(initial_wait) - REMOVED
                
                # Check for human verification page and error pages
                if self._is_human_verification_page():
                    logger.warning(f"Hit human verification page for {url}. Waiting for automatic resolution...")
                    
                    # Wait SIGNIFICANTLY longer for verification to complete automatically
                    max_verification_wait = 180  # Wait up to 3 minutes (180 seconds)
                    verification_check_interval = 10  # Check every 10 seconds instead of 5
                    
                    logger.info(f"Starting verification wait: up to {max_verification_wait}s with {verification_check_interval}s intervals...")
                    
                    for verification_attempt in range(max_verification_wait // verification_check_interval):
                        logger.debug(f"Verification wait attempt {verification_attempt + 1}: waiting {verification_check_interval}s...")
                        # time.sleep(verification_check_interval) - REMOVED
                        
                        # Check if verification has completed and session is still valid
                        if not self._is_human_verification_page():
                            total_wait_time = verification_attempt * verification_check_interval
                            logger.info(f"Human verification completed automatically after {total_wait_time}s")
                            
                            # Add extra wait after verification completes to ensure page is fully loaded
                            logger.debug("Adding extra 15s wait after verification completion...")
                            # time.sleep(15) - REMOVED
                            
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
                            # time.sleep(60)  # Wait a full minute after refresh - REMOVED
                            
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
                # time.sleep(20) - REMOVED
                
                # Double-check for verification page that might have appeared
                if self._is_human_verification_page():
                    logger.warning(f"Detected verification page on delayed check for {url}. Handling...")
                    # Use the same verification handling logic as above
                    max_verification_wait = 120  # Shorter wait for delayed detection
                    verification_check_interval = 10
                    
                    for verification_attempt in range(max_verification_wait // verification_check_interval):
                        logger.debug(f"Delayed verification check {verification_attempt + 1}: waiting {verification_check_interval}s...")
                        # time.sleep(verification_check_interval) - REMOVED
                        
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
                # time.sleep(delay) - REMOVED
        
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
    
    def _split_into_ranges(self, start_date: datetime, end_date: datetime, max_months: int = 2) -> List[tuple]:
        """Split date range into chunks of maximum months"""
        ranges = []
        current_start = start_date
        
        while current_start <= end_date:
            # Calculate end date by adding max_months using timedelta approximation
            # Using approximately 30 days per month for simplicity
            current_end = current_start + timedelta(days=(max_months * 30) - 1)
            
            # Don't go beyond the original end_date
            if current_end > end_date:
                current_end = end_date
            
            ranges.append((current_start, current_end))
            
            # Move to next range (start from the day after current_end)
            current_start = current_end + timedelta(days=1)
            
            # Safety check to avoid infinite loop
            if current_start > end_date:
                break
                
        logger.info(f"Split date range into {len(ranges)} chunks of max {max_months} months each")
        for i, (range_start, range_end) in enumerate(ranges, 1):
            logger.debug(f"Range {i}: {range_start.date()} to {range_end.date()}")
        return ranges
    
    def _scrape_date_range_with_picker(self, range_start: datetime, range_end: datetime) -> List[Dict]:
        """Scrape events for a date range using ForexFactory's date range picker"""
        events = []
        
        try:
            # Initialize driver if not present
            if not self.driver:
                logger.debug(f"Driver not initialized for range {range_start.date()} to {range_end.date()}, setting up fresh driver")
                self._setup_driver()
            
            # Format dates for the range picker input (format: "Oct 4, 2025 – Dec 1, 2025")
            start_formatted = range_start.strftime("%b %d, %Y")
            end_formatted = range_end.strftime("%b %d, %Y")
            date_range_str = f"{start_formatted} – {end_formatted}"
            
            # Open URL to the first day of the range
            month_abbr = range_start.strftime("%b").lower()
            day = range_start.day
            year = range_start.year
            date_str = f"{month_abbr}{day}.{year}"
            url = f"{self.base_url}?day={date_str}"
            
            logger.debug(f"Opening range picker for {range_start.date()} to {range_end.date()} - URL: {url}")
            
            # Navigate to the page
            if not self._navigate_to_page(url):
                logger.error(f"Failed to navigate to {url}")
                return []
            
            # Wait for page to load
            # time.sleep(random.uniform(2.0, 4.0)) - REMOVED
            
            try:
                # Click on the calendar options element with class "calendar__options left"
                logger.debug("Looking for calendar options element...")
                
                # Try multiple selectors for the calendar options element
                options_selectors = [
                    ".calendar__options.left",
                    ".calendar__options",
                    "[class*='calendar__options'][class*='left']",
                    ".calendar-options.left"
                ]
                
                options_element = None
                for selector in options_selectors:
                    try:
                        # options_element = self.wait.until(
                        #     EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        # )  # REMOVED - no WebDriverWait timeout
                        options_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        logger.debug(f"Found calendar options element with selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if not options_element:
                    raise NoSuchElementException("Could not find calendar options element with any selector")
                
                # Try to click using JavaScript if regular click fails
                try:
                    options_element.click()
                    logger.debug("Clicked on calendar options element using regular click")
                except Exception as click_error:
                    logger.debug(f"Regular click failed, trying JavaScript click: {click_error}")
                    # Use JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", options_element)
                    logger.debug("Clicked on calendar options element using JavaScript")
                
                # Wait a moment for the date range input to appear
                # time.sleep(1.0) - REMOVED
                
                # Find and fill the date range input
                logger.debug(f"Filling date range input with: {date_range_str}")
                # date_range_input = self.wait.until(
                #     EC.presence_of_element_located((By.ID, "calendar-date-range-1"))
                # )  # REMOVED - no WebDriverWait timeout
                date_range_input = self.driver.find_element(By.ID, "calendar-date-range-1")
                
                # Clear and fill the input
                date_range_input.clear()
                date_range_input.send_keys(date_range_str)
                logger.debug("Filled date range input")
                
                # Submit the form using Enter key instead of .submit() method
                # This works better when the element is not inside a form
                date_range_input.send_keys(Keys.RETURN)
                logger.debug("Submitted date range form using Enter key")
                
                # Wait 7 seconds as specified
                logger.debug("Waiting 7 seconds for date range to load...")
                # time.sleep(7.0) - REMOVED
                
                # Now scrape the entire table for the range
                logger.debug("Scraping calendar table for the date range...")
                events = self._scrape_calendar_table_for_range(range_start, range_end)
                
            except NoSuchElementException as e:
                logger.error(f"Could not find calendar options or date range input: {e}")
                return []
            except Exception as e:
                logger.error(f"Error using date range picker: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error in _scrape_date_range_with_picker: {e}")
            return []
        
        logger.info(f"Scraped {len(events)} events for range {range_start.date()} to {range_end.date()}")
        return events
    
    def _scrape_calendar_table_for_range(self, range_start: datetime, range_end: datetime) -> List[Dict]:
        """Scrape events from the calendar table for the entire date range"""
        events = []
        
        try:
            # Check if driver is still responsive
            if not self._is_driver_responsive():
                logger.error(f"WebDriver not responsive for range scraping {range_start.date()} to {range_end.date()}")
                return events
            
            # Wait for calendar table to load
            try:
                # self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'calendar__table')))  # REMOVED - no WebDriverWait timeout
                self.driver.find_element(By.CLASS_NAME, 'calendar__table')
                logger.debug("Calendar table found for range scraping")
            except NoSuchElementException:
                logger.warning(f"Calendar table not found for range {range_start.date()} to {range_end.date()}")
                return events
            
            # Wait a bit more for dynamic content
            # time.sleep(random.uniform(2.0, 4.0)) - REMOVED
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            if not page_source or len(page_source.strip()) == 0:
                logger.warning(f"Empty page source for range {range_start.date()} to {range_end.date()}")
                return events
                
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the calendar table
            calendar_table = soup.find('table', class_='calendar__table')
            if not calendar_table:
                logger.warning(f"No calendar table found for range {range_start.date()} to {range_end.date()}")
                return events
            
            # Find event rows
            tbody = calendar_table.find('tbody')
            if not tbody:
                logger.warning(f"No tbody found for range {range_start.date()} to {range_end.date()}")
                return events
            
            # Find all event rows and date headers
            rows = tbody.find_all(['tr'])
            logger.debug(f"Found {len(rows)} rows for range {range_start.date()} to {range_end.date()}")
            
            current_date = None
            for row in rows:
                row_classes = row.attrs.get('class', [])
                row_classes_str = ' '.join(row_classes)
                
                # Check if this is a date header row (try multiple possible class patterns)
                is_date_header = any(pattern in row_classes_str for pattern in [
                    'calendar__table-additional-row',
                    'calendar__date-header',
                    'calendar__header',
                    'additional-row'
                ])
                
                if is_date_header:
                    # This is a date header, try to extract the date from various cell patterns
                    date_cell = (row.find('td', class_='calendar__table-additional-row-cell') or
                               row.find('td', class_=lambda x: x and 'date' in x.lower() if x else False) or
                               row.find('td'))
                    
                    if date_cell:
                        date_text = date_cell.get_text(strip=True)
                        parsed_date = self._parse_date_header(date_text)
                        if parsed_date:
                            current_date = parsed_date
                            logger.debug(f"Found date header: {current_date.date()}")
                        else:
                            logger.debug(f"Could not parse date header text: '{date_text}'")
                    continue
                
                # Check if this is an event row (try multiple possible class patterns)
                is_event_row = any(pattern in row_classes_str for pattern in [
                    'calendar__row',
                    'calendar-row',
                    'event-row'
                ])
                
                if is_event_row:
                    # For range mode, be more lenient about date matching
                    # If we have a current_date, use it; otherwise try to parse date from the row
                    event_date = current_date
                    if not event_date:
                        # Try to extract date from the row itself
                        event_date = self._extract_date_from_event_row(row, range_start)
                    
                    # Only parse events if we have a valid event_date and it's within our range
                    if event_date and range_start <= event_date <= range_end:
                        try:
                            event = self._parse_event_row(row, event_date)
                            if event:
                                events.append(event)
                                logger.debug(f"Added event: {event.get('Event', 'Unknown')} on {event_date.date()}")
                        except Exception as e:
                            logger.error(f"Error parsing event row: {e}")
                            continue
                    else:
                        logger.debug(f"Skipping event row - event_date: {event_date}, in_range: {event_date and range_start <= event_date <= range_end if event_date else False}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error scraping calendar table for range: {e}")
        
        logger.info(f"Scraped {len(events)} events from calendar table for range {range_start.date()} to {range_end.date()}")
        return events
    
    def _extract_date_from_event_row(self, row, default_date: datetime) -> datetime:
        """Try to extract date from an event row when no date header is available"""
        try:
            # Look for date information in the row
            cells = row.find_all('td')
            if len(cells) > 0:
                first_cell = cells[0]
                cell_text = first_cell.get_text(strip=True)
                
                # Try to parse date from the first cell
                if cell_text:
                    parsed_date = self._parse_date_header(cell_text)
                    if parsed_date:
                        return parsed_date
        except Exception as e:
            logger.debug(f"Could not extract date from event row: {e}")
        
        # Return default date if we can't extract a specific date
        return default_date
    
    def _parse_date_header(self, date_text: str) -> Optional[datetime]:
        """Parse date header text to extract datetime"""
        try:
            # Handle different date formats that might appear in headers
            date_text = date_text.strip()
            
            if not date_text:
                return None
            
            # Try common ForexFactory date header formats
            formats = [
                "%a %b %d",      # "Sat Oct 4"
                "%a %B %d",      # "Sat October 4"
                "%a %b %d %Y",   # "Sat Oct 4 2025"
                "%a %B %d %Y",   # "Sat October 4 2025"
                "%A, %B %d",     # "Sunday, October 5"
                "%A, %b %d",     # "Sunday, Oct 5"
                "%A, %B %d %Y",  # "Sunday, October 5 2025"
                "%A, %b %d %Y",  # "Sunday, Oct 5 2025"
                "%B %d",         # "October 5"
                "%b %d",         # "Oct 5"
                "%B %d %Y",      # "October 5 2025"
                "%b %d %Y",      # "Oct 5 2025"
                "%d %b %Y",      # "5 Oct 2025"
                "%d %B %Y",      # "5 October 2025"
            ]
            
            current_year = datetime.now().year
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_text, fmt)
                    
                    # If year was not specified in the format, use current year
                    # but be smart about it - if we're in January and parsing December,
                    # it might be from the previous year, and vice versa
                    if parsed_date.year == 1900:  # Default year when not specified
                        parsed_date = parsed_date.replace(year=current_year)
                        
                        # Smart year adjustment for edge cases
                        current_month = datetime.now().month
                        if current_month == 1 and parsed_date.month == 12:
                            # If we're in January and parsing December, it's likely last year
                            parsed_date = parsed_date.replace(year=current_year - 1)
                        elif current_month == 12 and parsed_date.month == 1:
                            # If we're in December and parsing January, it might be next year
                            parsed_date = parsed_date.replace(year=current_year + 1)
                    
                    return parsed_date
                    
                except ValueError:
                    continue
            
            # If all formats failed, try some more flexible parsing
            try:
                # Try to extract date patterns with regex as fallback
                import re
                
                # Look for patterns like "Oct 4", "October 5", "4 Oct", etc.
                date_patterns = [
                    r'(\w+)\s+(\d+)',  # "Oct 4" or "4 Oct"
                    r'(\d+)\s+(\w+)',  # "4 Oct" (different order)
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, date_text)
                    if match:
                        # This would need more sophisticated parsing
                        # For now, just log and return None
                        logger.debug(f"Found potential date pattern '{match.groups()}' in '{date_text}' but cannot parse reliably")
                        break
                        
            except Exception:
                pass
            
            logger.debug(f"Could not parse date header: '{date_text}'")
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing date header '{date_text}': {e}")
            return None
    
    def scrape_single_day(self, target_date: datetime) -> List[Dict]:
        """Daily mode: scrape single date with fresh browser session"""
        try:
            logger.info(f"Starting DAILY scrape for {target_date.date()}")
            self._setup_driver()
            events = self._scrape_day(target_date, first_request=True)
            logger.info(f"Daily scrape completed: {len(events)} events found for {target_date.date()}")
            return events
        finally:
            self._close_driver()

    def scrape_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Range mode: scrape economic events for a date range using daily approach"""
        events = []
        
        try:
            # Calculate total days for reporting
            total_days = (end_date - start_date).days + 1
            
            logger.info(f"Starting RANGE-BASED scrape from {start_date.date()} to {end_date.date()}")
            logger.info(f"Total days in range: {total_days}")
            
            # Split the date range into chunks of exactly 1 month (hardcoded)
            ranges = self._split_into_ranges(start_date, end_date, max_months=1)
            
            total_ranges = len(ranges)
            successful_ranges = 0
            failed_ranges = 0
            
            logger.info(f"Processing {total_ranges} date range chunks")
            
            for i, (range_start, range_end) in enumerate(ranges, 1):
                logger.info(f"Processing range {i}/{total_ranges}: {range_start.date()} to {range_end.date()}")
                
                try:
                    # Scrape each day in the range using daily mode approach
                    range_events = self._scrape_range_by_days(range_start, range_end)
                    
                    if range_events is not None:
                        events.extend(range_events)
                        successful_ranges += 1
                        logger.info(f"Scraped {len(range_events)} events from range {range_start.date()} to {range_end.date()}")
                    else:
                        failed_ranges += 1
                        logger.warning(f"Failed to scrape range {range_start.date()} to {range_end.date()}")
                    
                    # Close driver after each range to start fresh session for next range
                    logger.debug("Closing driver after successful range scrape to start fresh session")
                    self._close_driver()
                    
                except Exception as range_error:
                    logger.error(f"Error processing range {range_start.date()} to {range_end.date()}: {range_error}")
                    failed_ranges += 1
                    continue
                
                # Random delay between ranges to avoid detection
                if i < total_ranges:  # Don't wait after the last range
                    delay = random.uniform(3.0, 8.0)
                    logger.debug(f"Waiting {delay:.1f} seconds before next range...")
                    # time.sleep(delay) - REMOVED
            
            # Calculate efficiency metrics for range-based approach
            success_rate = (successful_ranges / total_ranges * 100) if total_ranges > 0 else 0
            
            logger.info("=" * 60)
            logger.info("RANGE-BASED SCRAPING COMPLETED - SUMMARY REPORT")
            logger.info("=" * 60)
            logger.info(f"[TOTAL] Total events found: {len(events)}")
            logger.info(f"[RANGE] Date range: {start_date.date()} to {end_date.date()}")
            logger.info(f"[RANGES] Total ranges processed: {total_ranges}")
            logger.info(f"[SUCCESS] Successful ranges: {successful_ranges}/{total_ranges} ({success_rate:.1f}%)")
            logger.info(f"[FAILED] Failed ranges: {failed_ranges}")
            logger.info(f"[OPTIMIZATION] Using daily approach with monthly chunks")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during range-based scraping: {e}")
        finally:
            self._close_driver()
        
        return events
    
    def _scrape_range_by_days(self, range_start: datetime, range_end: datetime) -> List[Dict]:
        """Scrape a date range using ForexFactory range URL format"""
        try:
            # Initialize driver if not present
            if not self.driver:
                logger.debug(f"Driver not initialized for range {range_start.date()} to {range_end.date()}, setting up fresh driver")
                self._setup_driver()
            
            # Format dates for ForexFactory range URL format: mar22.2025-apr10.2025
            start_formatted = self._format_date_for_url(range_start)
            end_formatted = self._format_date_for_url(range_end)
            range_url = f"{self.base_url}?range={start_formatted}-{end_formatted}"
            
            logger.info(f"Using ForexFactory range URL: {range_url}")
            
            # Navigate to the range URL
            if not self._navigate_to_page(range_url):
                logger.error(f"Failed to navigate to range URL: {range_url}")
                # Fallback to daily scraping if range URL fails
                logger.info("Falling back to daily scraping approach")
                return self._scrape_range_by_daily_fallback(range_start, range_end)
            
            # Wait for page to load
            # time.sleep(random.uniform(3.0, 5.0)) - REMOVED
            
            # Check if driver is still responsive
            if not self._is_driver_responsive():
                logger.error(f"WebDriver not responsive for range {range_start.date()} to {range_end.date()}")
                return []
            
            # For range URLs, use HTML parsing directly since the page contains multiple days
            logger.info("Parsing range page using HTML table extraction")
            events = self._scrape_calendar_table_for_range(range_start, range_end)
            
            logger.info(f"Completed range scraping: {len(events)} total events from {range_start.date()} to {range_end.date()}")
            return events
            
        except Exception as e:
            logger.error(f"Error in _scrape_range_by_days: {e}")
            # Fallback to daily scraping if range approach fails
            logger.info("Falling back to daily scraping approach due to error")
            return self._scrape_range_by_daily_fallback(range_start, range_end)
    
    def _scrape_range_by_daily_fallback(self, range_start: datetime, range_end: datetime) -> List[Dict]:
        """Fallback method: scrape range by iterating through each day"""
        events = []
        current_date = range_start
        
        logger.info(f"Fallback: scraping range {range_start.date()} to {range_end.date()} day by day")
        
        while current_date <= range_end:
            try:
                # Skip weekends for efficiency (optional)
                if self._should_skip_date(current_date):
                    logger.debug(f"Skipping weekend date: {current_date.date()}")
                    current_date += timedelta(days=1)
                    continue
                
                logger.debug(f"Scraping day: {current_date.date()}")
                
                # Initialize driver if not present
                if not self.driver:
                    logger.debug(f"Driver not initialized for {current_date.date()}, setting up fresh driver")
                    self._setup_driver()
                
                # Scrape the day using the existing daily method
                day_events = self._scrape_day(current_date, first_request=(current_date == range_start))
                
                if day_events is not None:
                    events.extend(day_events)
                    logger.debug(f"Found {len(day_events)} events for {current_date.date()}")
                else:
                    logger.debug(f"No events found for {current_date.date()}")
                
                # Add delay between days to avoid being too aggressive
                # time.sleep(random.uniform(1.0, 3.0)) - REMOVED
                
            except Exception as e:
                logger.error(f"Error scraping day {current_date.date()}: {e}")
                # Continue with next day even if one fails
            
            # Move to next day
            current_date += timedelta(days=1)
        
        logger.info(f"Fallback completed: {len(events)} total events from {range_start.date()} to {range_end.date()}")
        return events
    
    def _format_date_for_url(self, date: datetime) -> str:
        """Format date for ForexFactory URL format: mar22.2025"""
        month_abbr = date.strftime("%b").lower()
        day = date.day
        year = date.year
        return f"{month_abbr}{day}.{year}"
    
    def _parse_js_calendar_data_for_range(self, calendar_data: Dict, range_start: datetime, range_end: datetime) -> List[Dict]:
        """Parse calendar data from JavaScript for a date range"""
        events = []
        
        try:
            # Navigate through the calendarComponentStates structure
            for key, calendar_state in calendar_data.items():
                if isinstance(calendar_state, dict) and 'days' in calendar_state:
                    for day_data in calendar_state['days']:
                        if 'events' in day_data:
                            # Check if this day is within our range
                            if 'dateline' in day_data and day_data['dateline']:
                                try:
                                    day_date = datetime.fromtimestamp(day_data['dateline'])
                                    if range_start <= day_date <= range_end:
                                        for event_data in day_data['events']:
                                            event = self._parse_js_event_data(event_data, day_date)
                                            if event:
                                                events.append(event)
                                except:
                                    # If we can't parse the date, include the events anyway
                                    for event_data in day_data['events']:
                                        event = self._parse_js_event_data(event_data, range_start)
                                        if event:
                                            events.append(event)
        
        except Exception as e:
            logger.error(f"Error parsing JavaScript calendar data for range: {e}")
        
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
                    # time.sleep(wait_time) - REMOVED
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
            # time.sleep(random.uniform(2.0, 4.0)) - REMOVED
            
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
        
        # CONVERSION AUTOMATIQUE DES IMPACTS - Convertir les classes CSS en valeurs lisibles
        events = self._convert_impact_in_events(events)
        
        # Save events immediately after scraping each day
        if events and self.csv_exporter:
            try:
                # Map events to trading pairs before saving
                mapped_events = self.symbol_mapper.map_events_to_pairs(events)
                # Use deduplication to append to existing CSV
                success = self.csv_exporter.append_with_deduplication(mapped_events)
                if success:
                    logger.info(f"Saved {len(mapped_events)} events for {date_str} to CSV")
                else:
                    logger.warning(f"Failed to save events for {date_str}")
            except Exception as save_error:
                logger.error(f"Error saving events for {date_str}: {save_error}")
        
        return events
    
    def _convert_impact_in_events(self, events: List[Dict]) -> List[Dict]:
        """Convertir automatiquement les classes CSS d'impact en valeurs lisibles"""
        for event in events:
            if 'Impact' in event:
                impact = event['Impact']
                # Convertir si c'est une classe CSS
                if 'Icon--Ff-Impact' in str(impact):
                    event['Impact'] = self._convert_css_impact_to_readable(impact)
                    logger.debug(f"Converted impact {impact} -> {event['Impact']}")
        return events
    
    def _extract_calendar_data_from_js(self, target_date: datetime) -> Optional[Dict]:
        """Extract calendarComponentStates data from JavaScript"""
        try:
            # Wait longer for JavaScript to load and execute
            # max_wait_time = 10  # REMOVED - no timeouts
            # wait_interval = 1   # REMOVED - no timeouts
            
            # Try to get JavaScript data immediately without waiting
            for attempt in range(3):  # Reduced attempts since no waiting
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
                
                if attempt < 2:  # Only 3 attempts total
                    logger.debug(f"calendarComponentStates not ready, retrying immediately...")
                    # No waiting - immediate retry
            
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
        try:
            # Check if there are any direct impact indicators in the event data
            if 'impact' in event_data:
                impact_value = str(event_data['impact'])
                # Handle CSS class names that might be stored directly
                if 'Icon--Ff-Impact' in impact_value:
                    return self._convert_css_impact_to_readable(impact_value)
                else:
                    logger.debug(f"Found direct impact in JS data: {impact_value}")
                    return impact_value.title()
            
            # Check for other possible impact field names
            impact_fields = ['impactLevel', 'impact_level', 'importance', 'priority', 'significance', 'impactClass', 'impact_class']
            for field in impact_fields:
                if field in event_data:
                    impact_value = str(event_data[field])
                    # Handle CSS class names that might be stored directly
                    if 'Icon--Ff-Impact' in impact_value:
                        return self._convert_css_impact_to_readable(impact_value)
                    else:
                        logger.debug(f"Found impact in field '{field}': {impact_value}")
                        return impact_value.title()
            
            # Check for ForexFactory-specific impact indicators in class names or CSS
            css_fields = ['className', 'class_name', 'cssClass', 'css_class', 'iconClass', 'icon_class']
            for field in css_fields:
                if field in event_data:
                    css_value = str(event_data[field]).lower()
                    if 'icon--ff-impact-red' in css_value or 'ff-impact-red' in css_value:
                        logger.debug(f"Found HIGH impact in CSS field '{field}': {css_value}")
                        return 'High'
                    elif 'icon--ff-impact-ora' in css_value or 'ff-impact-ora' in css_value:
                        logger.debug(f"Found MEDIUM impact in CSS field '{field}': {css_value}")
                        return 'Medium'
                    elif 'icon--ff-impact-yel' in css_value or 'ff-impact-yel' in css_value:
                        logger.debug(f"Found LOW impact in CSS field '{field}': {css_value}")
                        return 'Low'
            
            # Check numeric indicators that might represent impact levels
            # ForexFactory might use 1=Low, 2=Medium, 3=High or similar
            numeric_impact_indicators = ['impactNum', 'impact_num', 'level', 'strength', 'impactLevel']
            for field in numeric_impact_indicators:
                if field in event_data:
                    try:
                        impact_num = int(event_data[field])
                        if impact_num >= 3:
                            return 'High'
                        elif impact_num >= 2:
                            return 'Medium'
                        else:
                            return 'Low'
                    except (ValueError, TypeError):
                        continue
            
            # Check for string-based impact indicators
            string_impact_indicators = ['impactString', 'impact_string', 'impactText', 'impact_text']
            for field in string_impact_indicators:
                if field in event_data:
                    impact_str = str(event_data[field]).lower()
                    if 'high' in impact_str or 'red' in impact_str:
                        return 'High'
                    elif 'medium' in impact_str or 'orange' in impact_str:
                        return 'Medium'
                    elif 'low' in impact_str or 'yellow' in impact_str:
                        return 'Low'
            
            # Log the available fields for debugging
            logger.debug(f"Available JS event fields for impact: {list(event_data.keys())}")
            
        except Exception as e:
            logger.debug(f"Error extracting impact from JS data: {e}")
            
        return 'Low'  # Default impact level
    
    def _convert_css_impact_to_readable(self, css_impact: str) -> str:
        """Convert CSS impact class to readable impact level"""
        css_impact_lower = css_impact.lower()
        
        # Check if it's already a readable value
        if css_impact_lower in ['high', 'medium', 'low']:
            return css_impact.title()
        
        # Convert CSS classes to readable values
        if 'icon--ff-impact-red' in css_impact_lower or 'ff-impact-red' in css_impact_lower:
            return 'High'
        elif 'icon--ff-impact-ora' in css_impact_lower or 'ff-impact-ora' in css_impact_lower:
            return 'Medium'
        elif 'icon--ff-impact-yel' in css_impact_lower or 'ff-impact-yel' in css_impact_lower:
            return 'Low'
        elif 'icon--ff-impact-gra' in css_impact_lower or 'ff-impact-gra' in css_impact_lower:
            return 'Low'
        else:
            return 'Low'  # Default fallback
    
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
                                    # Always update impact from HTML as it's more reliable
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
                # self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'calendar__table')))  # REMOVED - no WebDriverWait timeout
                self.driver.find_element(By.CLASS_NAME, 'calendar__table')
                logger.debug("Calendar table found for HTML fallback")
            except NoSuchElementException:
                logger.warning(f"Calendar table not found for {date_str}")
                return events
            except Exception as e:
                logger.error(f"Error waiting for calendar table: {e}")
                return events
            
            # Wait a bit more for dynamic content
            # time.sleep(random.uniform(1.0, 2.0)) - REMOVED
            
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
            # time.sleep(random.uniform(2.0, 5.0)) - REMOVED
            
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
            if len(cells) < 3:  # Minimum required cells
                return None
            
            # Dynamically detect column structure based on CSS classes and content
            time_cell = None
            currency_cell = None
            impact_cell = None
            event_cell = None
            actual_cell = None
            forecast_cell = None
            previous_cell = None
            
            # Find cells by their CSS classes and content patterns
            for i, cell in enumerate(cells):
                cell_classes = ' '.join(cell.get('class', []))
                cell_text = cell.get_text(strip=True)
                
                # Time cell - usually first or has time-related classes
                if i == 0 or 'time' in cell_classes.lower() or self._is_time_cell(cell_text):
                    time_cell = cell
                
                # Currency cell - contains currency codes or links
                elif 'currency' in cell_classes.lower() or self._is_currency_cell(cell_text, cell):
                    currency_cell = cell
                
                # Impact cell - has impact-related classes
                elif 'impact' in cell_classes.lower() or 'calendar__impact' in cell_classes:
                    impact_cell = cell
                
                # Event cell - contains event names, usually has links
                elif 'event' in cell_classes.lower() or self._is_event_cell(cell_text, cell):
                    event_cell = cell
                
                # Data cells (Actual/Forecast/Previous) - contain numbers or N/A
                elif self._is_data_cell(cell_text):
                    if actual_cell is None:
                        actual_cell = cell
                    elif forecast_cell is None:
                        forecast_cell = cell
                    elif previous_cell is None:
                        previous_cell = cell
            
            # Fallback: if we couldn't detect some cells, use positional logic as backup
            if not time_cell and len(cells) > 0:
                time_cell = cells[0]
            if not currency_cell and len(cells) > 1:
                currency_cell = cells[1]
            if not impact_cell and len(cells) > 2:
                impact_cell = cells[2]
            if not event_cell and len(cells) > 3:
                event_cell = cells[3]
            if not actual_cell and len(cells) > 4:
                actual_cell = cells[4]
            if not forecast_cell and len(cells) > 5:
                forecast_cell = cells[5]
            if not previous_cell and len(cells) > 6:
                previous_cell = cells[6]
            
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
            
            # Only return event if we have a valid event name
            if not event_name or event_name.strip() == '':
                logger.debug(f"Skipping event row with no event name. Currency: {currency}, Impact: {impact}")
                return None
            
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
    
    def _is_time_cell(self, cell_text: str) -> bool:
        """Check if cell contains time information"""
        if not cell_text:
            return False
        
        # Check for time patterns
        time_patterns = [
            r'\d{1,2}:\d{2}',  # HH:MM
            r'\d{1,2}:\d{2}[AP]M',  # HH:MM AM/PM
            r'all day',  # All Day
            r'tbd',  # TBD
        ]
        
        import re
        for pattern in time_patterns:
            if re.search(pattern, cell_text.lower()):
                return True
        return False
    
    def _is_currency_cell(self, cell_text: str, cell) -> bool:
        """Check if cell contains currency information"""
        if not cell_text:
            return False
        
        # Check for currency codes
        currency_codes = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD', 'CNY']
        if cell_text.upper() in currency_codes:
            return True
        
        # Check for currency links
        if cell.find('a') and cell.find('a').get_text(strip=True).upper() in currency_codes:
            return True
        
        return False
    
    def _is_event_cell(self, cell_text: str, cell) -> bool:
        """Check if cell contains event information"""
        if not cell_text:
            return False
        
        # Check for event links
        if cell.find('a'):
            return True
        
        # Check for common event keywords
        event_keywords = ['bank holiday', 'speaks', 'meeting', 'rate', 'gdp', 'inflation', 'employment']
        if any(keyword in cell_text.lower() for keyword in event_keywords):
            return True
        
        return False
    
    def _is_data_cell(self, cell_text: str) -> bool:
        """Check if cell contains data (Actual/Forecast/Previous)"""
        if not cell_text:
            return False
        
        # Check for data patterns
        data_patterns = [
            r'^\d+\.?\d*%?$',  # Numbers with optional decimal and %
            r'^\d+\.?\d*[KMB]?$',  # Numbers with K/M/B suffixes
            r'^n/a$',  # N/A
            r'^-$',  # Dash
            r'^$',  # Empty
        ]
        
        import re
        for pattern in data_patterns:
            if re.match(pattern, cell_text.lower()):
                return True
        return False

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
        
        # Get the HTML content of the cell
        cell_html = str(impact_cell).lower()
        
        # Debug logging to understand the structure
        logger.debug(f"Parsing impact cell HTML: {cell_html[:200]}...")
        
        # Check if we're getting CSS class names instead of converted values
        if 'icon--ff-impact' in cell_html:
            logger.debug(f"Found ForexFactory impact classes in HTML: {cell_html[:100]}")
            # Log the specific classes found
            if 'icon--ff-impact-red' in cell_html:
                logger.debug("Should return HIGH impact")
            elif 'icon--ff-impact-ora' in cell_html:
                logger.debug("Should return MEDIUM impact")
            elif 'icon--ff-impact-yel' in cell_html:
                logger.debug("Should return LOW impact")
        
        # Look for common ForexFactory impact indicators
        # Check for classes that typically indicate impact levels
        high_indicators = [
            'impact-high', 'high-impact', 'cal_high', 'icon-high',
            'red', 'color-red', 'bg-red', 'impact_high', 'ff-impact-high',
            'impactlevel-high', 'impact_level_high', 'priority-high',
            'icon--ff-impact-red', 'ff-impact-red'
        ]
        medium_indicators = [
            'impact-medium', 'medium-impact', 'cal_medium', 'icon-medium',
            'orange', 'color-orange', 'bg-orange', 'impact_medium', 'yellow',
            'ff-impact-medium', 'impactlevel-medium', 'impact_level_medium',
            'priority-medium', 'amber',
            'icon--ff-impact-ora', 'ff-impact-ora'
        ]
        low_indicators = [
            'impact-low', 'low-impact', 'cal_low', 'icon-low',
            'yellow', 'color-yellow', 'bg-yellow', 'impact_low',
            'ff-impact-low', 'impactlevel-low', 'impact_level_low',
            'priority-low',
            'icon--ff-impact-yel', 'ff-impact-yel'
        ]
        
        if any(indicator in cell_html for indicator in high_indicators):
            logger.debug("Found HIGH impact indicator - returning 'High'")
            return 'High'
        elif any(indicator in cell_html for indicator in medium_indicators):
            logger.debug("Found MEDIUM impact indicator - returning 'Medium'")
            return 'Medium'
        elif any(indicator in cell_html for indicator in low_indicators):
            logger.debug("Found LOW impact indicator - returning 'Low'")
            return 'Low'
        
        # Check for text content directly
        cell_text = impact_cell.get_text(strip=True).lower()
        if any(text in cell_text for text in ['high', 'red', 'high impact expected']):
            return 'High'
        elif any(text in cell_text for text in ['medium', 'orange', 'medium impact expected']):
            return 'Medium'
        elif any(text in cell_text for text in ['low', 'yellow', 'low impact expected']):
            return 'Low'
        
        # Look for specific div or span classes that might contain impact info
        try:
            # Check for elements with class attributes that might indicate impact
            for element in impact_cell.find_all(['div', 'span', 'img']):
                element_classes = element.get('class', [])
                element_classes_str = ' '.join(element_classes).lower()
                
                if any(clazz in element_classes_str for clazz in [
                    'high', 'medium', 'low', 'red', 'orange', 'yellow',
                    'icon--ff-impact-red', 'icon--ff-impact-ora', 'icon--ff-impact-yel',
                    'ff-impact-red', 'ff-impact-ora', 'ff-impact-yel'
                ]):
                    if ('high' in element_classes_str or 'red' in element_classes_str or 
                        'icon--ff-impact-red' in element_classes_str or 'ff-impact-red' in element_classes_str):
                        return 'High'
                    elif ('medium' in element_classes_str or 'orange' in element_classes_str or
                          'icon--ff-impact-ora' in element_classes_str or 'ff-impact-ora' in element_classes_str):
                        return 'Medium'
                    elif ('low' in element_classes_str or 'yellow' in element_classes_str or
                          'icon--ff-impact-yel' in element_classes_str or 'ff-impact-yel' in element_classes_str):
                        return 'Low'
            
            # Check for style attributes that might indicate color coding
            style_attr = impact_cell.get('style', '').lower()
            if 'red' in style_attr or 'background-color: red' in style_attr:
                return 'High'
            elif 'orange' in style_attr or 'yellow' in style_attr or 'background-color: orange' in style_attr:
                return 'Medium'
            
            # Check for data attributes that might contain impact information
            for attr_name, attr_value in impact_cell.attrs.items():
                if 'data-' in attr_name.lower() and isinstance(attr_value, str):
                    attr_value_lower = attr_value.lower()
                    if any(indicator in attr_value_lower for indicator in high_indicators):
                        return 'High'
                    elif any(indicator in attr_value_lower for indicator in medium_indicators):
                        return 'Medium'
                    elif any(indicator in attr_value_lower for indicator in low_indicators):
                        return 'Low'
                
        except Exception as e:
            logger.debug(f"Error parsing impact cell classes: {e}")
        
        # Debug: log what was found before defaulting to Low
        logger.debug(f"No impact indicators found in cell, defaulting to Low. Cell text: '{cell_text}', HTML: {cell_html[:100]}")
        
        # Default to Low if no other indicators found
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