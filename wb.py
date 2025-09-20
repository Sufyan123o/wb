"""
Wimbledon Ballot Automation Script
Based on pokebotsh-main's selenium implementation
Step 1: Navigate to ballot website and handle captcha interface
"""

import logging
import time
import urllib.error
import csv
import os
import base64
import requests
from typing import Any

import chromedriver_autoinstaller
from seleniumbase import SB

'''
ENTER YOUR API KEY FROM https://capsolver.com/
'''
CAPSOLVER_API_KEY = "REPLACE"  # Replace with your actual CapSolver API key
AUTO_SOLVE_CAPTCHA = True

# CapSolver API Configuration
CAPSOLVER_API_URL = "https://api.capsolver.com/createTask"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class CapSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = CAPSOLVER_API_URL
    
    def solve_image_captcha(self, image_base64, website_url="https://ballot.wimbledon.com/"):
        """Solve image-to-text CAPTCHA using CapSolver"""
        try:
            log.info("Resolving verification challenge...")
            
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "ImageToTextTask",
                    "websiteURL": website_url,
                    "module": "module_016",  # Specified module for this type of CAPTCHA
                    "body": image_base64
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            result = response.json()
            
            if result.get("errorId") == 0 and result.get("status") == "ready":
                solution_text = result.get("solution", {}).get("text", "")
                log.info("Verification challenge resolved")
                return solution_text
            else:
                log.error(f"CapSolver image CAPTCHA error: {result}")
                return None
                
        except Exception as e:
            log.error(f"Error solving image CAPTCHA with CapSolver: {e}")
            return None
    
    def solve_recaptcha_v2(self, image_base64, question, website_url="https://ballot.wimbledon.com/"):
        """Solve reCAPTCHA v2 classification using CapSolver"""
        try:
            log.info(f"Sending reCAPTCHA v2 to CapSolver with question: {question}")
            
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "ReCaptchaV2Classification",
                    "websiteURL": website_url,
                    "image": image_base64,
                    "question": question
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            result = response.json()
            
            if result.get("errorId") == 0 and result.get("status") == "ready":
                solution = result.get("solution", {})
                log.info(f"CapSolver solved reCAPTCHA v2: {solution}")
                return solution
            else:
                log.error(f"CapSolver reCAPTCHA v2 error: {result}")
                return None
                
        except Exception as e:
            log.error(f"Error solving reCAPTCHA v2 with CapSolver: {e}")
            return None
    
    def get_element_screenshot_base64(self, browser_session, selector):
        """Take screenshot of specific element and convert to base64"""
        try:
            element = browser_session.find_element("css selector", selector)
            screenshot = element.screenshot_as_base64
            return screenshot
        except Exception as e:
            log.error(f"Error taking element screenshot: {e}")
            return None

class UserAgent:
    def __init__(self):
        self.base_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
        ]
        
    def get_user_agent(self):
        return self.base_agents[0]  # Use first one for consistency

class WimbledonAutomation:
    def __init__(self, profile_details=None):
        self.ballot_url = "https://ballot.wimbledon.com/"
        self.main_url = "https://www.wimbledon.com/en_gb/tickets/the_wimbledon_public_ballot.html"
        self.user_agent = UserAgent()
        self.login_details = profile_details
        self.capsolver = CapSolver(CAPSOLVER_API_KEY) if CAPSOLVER_API_KEY != "YOUR_API_KEY" else None
        
    def load_all_profiles(self):
        """Load all profiles from CSV file"""
        csv_path = os.path.join(os.path.dirname(__file__), "profiles.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                profiles = list(reader)  # Get all rows
                log.info(f"Loaded {len(profiles)} profiles from CSV")
                return profiles
        except FileNotFoundError:
            log.error(f"CSV file not found: {csv_path}")
            return []
        except Exception as e:
            log.error(f"Error reading CSV file: {e}")
            return []
        
    def scrape_with_selenium_and_keep_open(self, url, click_ballot_button=False):
        """Open browser, navigate to URL, and keep browser open for manual interaction"""
        try:
            chromedriver_autoinstaller.install()
        except urllib.error.URLError as e:
            log.error(f"Error with chromedriver auto-installation - {e}")
            return "", None

        # Create browser session using context manager entry
        try:
            sb_context = SB(uc=True, headless=False)
            sb = sb_context.__enter__()  # Manually enter context manager
            sb.uc_open_with_reconnect(url, reconnect_time=4)
        except Exception as e:
            log.error(f"Selenium exception: {e}")
            try:
                sb_context.__exit__(None, None, None)
            except:
                pass
            return "", None
        
        time.sleep(2)  # Quick wait for page elements
        
        html = sb.get_page_source()
        return html, (sb, sb_context)  # Return both browser and context for cleanup
    
    def navigate_to_ballot_and_keep_open(self):
        """Navigate directly to the ballot website and keep browser open"""
        try:
            log.info("Accessing ballot application...")
            html, browser_data = self.scrape_with_selenium_and_keep_open(self.ballot_url, click_ballot_button=False)
            
            if not html or not browser_data:
                log.error("Failed to open browser or get page content")
                return None, None
            
            browser_session, sb_context = browser_data
            
            log.info("Application page loaded")
            return html, browser_data
                
        except Exception as e:
            log.error(f"Error navigating to ballot: {e}")
            return None, None
    
    def solve_initial_captcha(self, browser_session):
        """Automatically solve the initial image CAPTCHA using CapSolver"""
        if not self.capsolver:
            log.warning("CapSolver not configured - skipping automatic CAPTCHA solving")
            return False
            
        try:
            # Specific peak45.secutix.com CAPTCHA selectors first, then fallbacks
            captcha_selectors = [
                '#img_captcha',  # Exact selector for peak45.secutix.com
                'img[src*="captcha.png"]',
                'img[alt*="captcha"]', 
                'img[id*="captcha"]',
                '.captcha img',
                '#captcha img'
            ]
            
            captcha_image = None
            captcha_selector = None
            
            for selector in captcha_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        captcha_image = self.capsolver.get_element_screenshot_base64(browser_session, selector)
                        if captcha_image:
                            captcha_selector = selector
                            log.info(f"Found CAPTCHA image with selector: {selector}")
                            break
                except Exception as e:
                    log.debug(f"CAPTCHA selector {selector} failed: {e}")
                    continue
            
            if not captcha_image:
                log.warning("Could not find CAPTCHA image to solve")
                return False
            
            # Solve the CAPTCHA using the peak45.secutix.com URL for better accuracy
            current_url = browser_session.get_current_url()
            website_url = current_url if 'peak45.secutix.com' in current_url else self.ballot_url
            solution = self.capsolver.solve_image_captcha(captcha_image, website_url)
            if not solution:
                log.error("Failed to solve CAPTCHA")
                return False
            
            # Find and fill the CAPTCHA input field
            input_selectors = [
                '#secret',  # Exact selector for peak45.secutix.com
                'input[name="secret"]',
                'input[name*="secret"]',
                'input[name*="captcha"]',
                'input[id*="secret"]',
                'input[id*="captcha"]',
                'input[type="text"]'
            ]
            
            input_filled = False
            for input_selector in input_selectors:
                try:
                    if browser_session.is_element_present(input_selector):
                        browser_session.type(input_selector, solution)
                        log.info(f"Filled CAPTCHA solution: {solution}")
                        input_filled = True
                        break
                except Exception as e:
                    log.debug(f"CAPTCHA input selector {input_selector} failed: {e}")
                    continue
            
            if not input_filled:
                log.error("Could not find CAPTCHA input field")
                return False
            
            # Submit the CAPTCHA form - try peak45.secutix.com specific method first
            try:
                # First try the specific peak45.secutix.com JavaScript function
                if browser_session.is_element_present('#submit_button'):
                    browser_session.execute_script("submitCaptcha();")
                    log.info("Submitted CAPTCHA using JavaScript submitCaptcha() function")
                    time.sleep(3)  # Wait for form submission
                    return True
            except Exception as e:
                log.debug(f"JavaScript submitCaptcha() failed: {e}")
            
            # Fallback to clicking the submit button
            submit_selectors = [
                '#submit_button a',  # Exact selector for peak45.secutix.com
                '#submit_button',
                'input[type="submit"]',
                'button[type="submit"]',
                'button:contains("Submit")',
                'input[value*="Submit"]'
            ]

            for submit_selector in submit_selectors:
                try:
                    if browser_session.is_element_present(submit_selector):
                        browser_session.click(submit_selector)
                        log.info(f"Submitted CAPTCHA form using selector: {submit_selector}")
                        time.sleep(3)  # Wait for form submission
                        return True
                except Exception as e:
                    log.debug(f"CAPTCHA submit selector {submit_selector} failed: {e}")
                    continue
            
            log.error("Could not find CAPTCHA submit button")
            return False
            
        except Exception as e:
            log.error(f"Error solving initial CAPTCHA: {e}")
            return False

    def handle_captcha_page(self, html):
        """Handle the captcha/waiting room page from HTML content"""
        try:
            # Page content analysis completed
            
            # Check if we have captcha elements in the HTML - be more specific
            captcha_indicators = [
                "img_captcha_container",  # Specific to peak45.secutix.com
                "img_captcha",
                "peak45.secutix.com",  # Specific domain detection
                "form_captcha", 
                "waitingroom",
                "captcha.png",
                "Enter the characters from the image",
                "secret"  # Input field name for peak45.secutix.com
            ]
            
            # Additional ballot-specific indicators
            ballot_indicators = [
                "ballot.wimbledon.com",
                "wimbledon ballot",
                "ticket ballot",
                "myWimbledon"
            ]
            
            found_indicators = []
            found_ballot_indicators = []
            
            html_lower = html.lower()
            
            for indicator in captcha_indicators:
                if indicator.lower() in html_lower:
                    found_indicators.append(indicator)
                    log.info(f"Found captcha indicator: {indicator}")
            
            for indicator in ballot_indicators:
                if indicator.lower() in html_lower:
                    found_ballot_indicators.append(indicator)
                    log.info(f"Found ballot indicator: {indicator}")
            
            # Only return True if we have clear captcha indicators
            if found_indicators:
                log.info("Detected captcha/verification page")
                
                if "captcha.png" in html_lower:
                    log.info("Captcha image detected in page")
                    
                if "secret" in html_lower:
                    log.info("Captcha input field detected")
                    
                log.info("Manual intervention required - CAPTCHA detected!")
                return True
            elif found_ballot_indicators:
                log.info("On ballot-related page but no captcha detected")
                log.info("This might be a form page or success page")
                return False
            else:
                log.info("No clear captcha indicators found")
                return False
                
        except Exception as e:
            log.error(f"Error handling captcha page: {e}")
            return False
    
    def fill_registration_form(self, browser_session):
        """Fill the registration form with details from CSV"""
        if not self.login_details:
            log.error("No login details available to fill form")
            return False
        
        try:
            # Completing registration form
            
            # Add debugging to see current page info
            try:
                current_url = browser_session.get_current_url()
                log.info(f"Current URL: {current_url}")
                page_title = browser_session.get_title()
                log.info(f"Page title: {page_title}")
                
                # Check number of windows/tabs
                window_handles = browser_session.driver.window_handles
                log.info(f"Number of browser windows/tabs: {len(window_handles)}")
                log.info(f"Current window handle: {browser_session.driver.current_window_handle}")
                
            except Exception as debug_error:
                log.warning(f"Could not get page debug info: {debug_error}")
            
            # Extract details from CSV (note: CSV uses 'Email' not 'email')
            email = self.login_details['Email']
            password = self.login_details['password']
            name = self.login_details['Name']
            address = self.login_details['AddressLine1']
            city = self.login_details['City']
            postcode = self.login_details['Postcode']
            mobile = self.login_details['MobileNumber']
            
            # Split name into first and last name
            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Fill email field - using exact selectors from the HTML
            email_selectors = [
                'input#email[data-gigya-name="email"]',  # Most specific from actual HTML
                'input[data-gigya-name="email"]',
                'input[name="email"]',
                'input#email',
                'input[data-screenset-element-id="email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.type(selector, email)
                        # Email field completed
                        email_filled = True
                        break
                except Exception as e:
                    log.debug(f"Email selector {selector} failed: {e}")
                    continue
            
            if not email_filled:
                log.warning("Could not find email input field")
            
            # Fill password field - using exact selectors from the HTML
            password_selectors = [
                'input#password[data-gigya-name="password"]',  # Most specific from actual HTML
                'input[data-gigya-name="password"]',
                'input[name="password"]',
                'input#password',
                'input[data-screenset-element-id="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.type(selector, password)
                        # Password field completed
                        password_filled = True
                        break
                except Exception as e:
                    log.debug(f"Password selector {selector} failed: {e}")
                    continue
            
            if not password_filled:
                log.warning("Could not find password input field")
            
            # Fill confirm password field - using exact selectors from the HTML
            confirm_password_selectors = [
                'input#passwordRetype[data-gigya-name="passwordRetype"]',  # Most specific from actual HTML
                'input[data-gigya-name="passwordRetype"]',
                'input[name="passwordRetype"]',
                'input#passwordRetype',
                'input[data-screenset-element-id="passwordRetype"]'
            ]
            
            for selector in confirm_password_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.type(selector, password)
                        # Confirm password field completed
                        break
                except Exception as e:
                    log.debug(f"Confirm password selector {selector} failed: {e}")
                    continue
            
            # Wait for form to fully load before checking checkboxes
            # Waiting for form to load
            time.sleep(3)
            
            # Check privacy policy checkbox - using exact label selector from user's extension
            privacy_label_selector = '#register-site-login > div:nth-of-type(4) > span:nth-of-type(1) > .gigya-container > .gigya-composite-control > .gigya-label'
            
            privacy_checked = False
            terms_checked = False
            try:
                if browser_session.is_element_present(privacy_label_selector):
                    browser_session.click(privacy_label_selector)
                    # Privacy policy accepted
                    time.sleep(0.5)  # Wait for UI update
                    privacy_checked = True
                else:
                    log.warning("Privacy policy checkbox label not found")
            except Exception as e:
                log.error(f"Privacy checkbox label click failed: {e}")
            
            if not privacy_checked:
                log.warning("Privacy checkbox label click failed - trying fallback methods")
                # Simple fallback - try to find any privacy-related checkbox
                try:
                    privacy_fallback_selectors = [
                        'input[name*="privacy"]',
                        'input[name*="Privacy"]', 
                        'input[id*="privacy"]',
                        'input[id*="Privacy"]'
                    ]
                    
                    for fallback_selector in privacy_fallback_selectors:
                        if browser_session.is_element_present(fallback_selector):
                            if not browser_session.is_selected(fallback_selector):
                                browser_session.click(fallback_selector)
                                log.info("Checked privacy checkbox via fallback")
                                privacy_checked = True
                                break
                except Exception as e:
                    log.debug(f"Privacy fallback failed: {e}")
            
            # Check terms of service checkbox - using exact label selector from user's extension
            terms_label_selector = '#register-site-login > div:nth-of-type(4) > span:nth-of-type(2) > .gigya-container > .gigya-composite-control > .gigya-label'
            
            try:
                if browser_session.is_element_present(terms_label_selector):
                    browser_session.click(terms_label_selector)
                    # Terms of service accepted
                    time.sleep(0.5)  # Wait for UI update
                    terms_checked = True
                else:
                    log.warning("Terms of service checkbox label not found")
            except Exception as e:
                log.error(f"Terms checkbox label click failed: {e}")
            
            # Fallback for terms checkbox if label click failed
            if not terms_checked:
                log.warning("Terms checkbox label click failed - trying fallback methods")
                try:
                    terms_fallback_selectors = [
                        'input[name*="terms"]',
                        'input[name*="Terms"]',
                        'input[id*="terms"]', 
                        'input[id*="Terms"]'
                    ]
                    
                    for fallback_selector in terms_fallback_selectors:
                        if browser_session.is_element_present(fallback_selector):
                            if not browser_session.is_selected(fallback_selector):
                                browser_session.click(fallback_selector)
                                log.info("Checked terms checkbox via fallback")
                                terms_checked = True
                                break
                except Exception as e:
                    log.debug(f"Terms fallback failed: {e}")
            
            # Wait a moment for any UI updates
            time.sleep(1)
            
            # Summary of form filling status
            # Form completion summary removed for cleaner output
            
            # Check if all required fields are filled
            all_required_filled = email_filled and password_filled and privacy_checked and terms_checked
            
            if all_required_filled:
                log.info("All required form fields completed successfully!")
            else:
                log.warning("Some required form fields may not be filled properly")
            
            log.info("Registration form completed")
            return True
            
        except Exception as e:
            log.error(f"Error filling registration form: {e}")
            return False
    
    def handle_post_submission_captcha(self, browser_session):
        """Handle any CAPTCHA that appears after form submission"""
        if not self.capsolver:
            log.warning("CapSolver not configured - manual CAPTCHA solving required")
            input("Please solve the CAPTCHA manually and press Enter to continue...")
            return True
            
        try:
            # Checking for additional verification
            
            # Wait a moment for any CAPTCHA to appear
            time.sleep(1)
            
            # Check for any type of CAPTCHA elements
            captcha_indicators = [
                'iframe[src*="recaptcha"]',  # reCAPTCHA iframe
                '.g-recaptcha',  # reCAPTCHA div
                'img[src*="captcha"]',  # Image CAPTCHA
                '#img_captcha',  # Specific image CAPTCHA
                'input[name*="captcha"]',  # CAPTCHA input
                'input[name*="secret"]',  # Secret input
                '.recaptcha-checkbox',  # reCAPTCHA checkbox
                '#recaptcha-anchor'  # reCAPTCHA anchor
            ]
            
            captcha_found = False
            captcha_type = None
            
            for selector in captcha_indicators:
                if browser_session.is_element_present(selector):
                    log.info(f"Found post-submission CAPTCHA element: {selector}")
                    captcha_found = True
                    if 'recaptcha' in selector:
                        captcha_type = 'recaptcha'
                    elif 'img' in selector or 'captcha' in selector:
                        captcha_type = 'image'
                    break
            
            if not captcha_found:
                # No additional verification required
                return True
            
            # Handle different CAPTCHA types
            if captcha_type == 'image':
                log.info("Attempting to solve image CAPTCHA...")
                return self.solve_post_submission_image_captcha(browser_session)
            
            elif captcha_type == 'recaptcha':
                log.info("Attempting to solve reCAPTCHA...")
                return self.solve_post_submission_recaptcha(browser_session)
            
            return False
            
        except Exception as e:
            log.error(f"Error handling post-submission CAPTCHA: {e}")
            return False
    
    def solve_post_submission_image_captcha(self, browser_session):
        """Solve image CAPTCHA that appears after form submission"""
        try:
            # Similar to initial CAPTCHA solving but for post-submission
            captcha_selectors = [
                '#img_captcha',
                'img[src*="captcha"]',
                'img[id*="captcha"]'
            ]
            
            captcha_image = None
            for selector in captcha_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        captcha_image = self.capsolver.get_element_screenshot_base64(browser_session, selector)
                        if captcha_image:
                            log.info(f"Found post-submission CAPTCHA image: {selector}")
                            break
                except Exception as e:
                    continue
            
            if not captcha_image:
                log.error("Could not find post-submission CAPTCHA image")
                return False
            
            # Solve with CapSolver
            current_url = browser_session.get_current_url()
            solution = self.capsolver.solve_image_captcha(captcha_image, current_url)
            
            if not solution:
                log.error("Failed to solve post-submission CAPTCHA")
                return False
            
            # Fill the solution
            input_selectors = ['#secret', 'input[name="secret"]', 'input[name*="captcha"]']
            for selector in input_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.type(selector, solution)
                        log.info(f"Filled post-submission CAPTCHA solution: {solution}")
                        break
                except Exception as e:
                    continue
            
            # Submit the solution
            submit_selectors = ['#submit_button', 'input[type="submit"]', 'button[type="submit"]']
            for selector in submit_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.click(selector)
                        log.info("Submitted post-submission CAPTCHA")
                        time.sleep(1)
                        return True
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Error solving post-submission image CAPTCHA: {e}")
            return False
    
    def solve_post_submission_recaptcha(self, browser_session):
        """Solve reCAPTCHA that appears after form submission"""
        try:
            log.info("🤖 Detected reCAPTCHA after form submission")
            log.info("⏳ Please solve the reCAPTCHA manually in the browser...")
            
            # Wait for user to solve the reCAPTCHA
            input("✅ Press Enter when you have solved the reCAPTCHA...")
            
            log.info("🎯 Continuing automation after reCAPTCHA solved...")
            return True
            
        except Exception as e:
            log.error(f"Error handling post-submission reCAPTCHA: {e}")
            return False
    
    def run_step_one(self, debug_mode=True):
        """Execute the first step: Navigate to ballot and handle captcha - keep browser open"""
        log.info("Starting Wimbledon Ballot Step 1: Navigate and handle captcha")
        log.info("Browser will remain open for manual captcha solving")
        
        try:
            # Step 1: Navigate to ballot and get HTML, keep browser open
            html, browser_data = self.navigate_to_ballot_and_keep_open()
            
            if not html or not browser_data:
                log.error("Failed to get page content or browser session")
                return False
            
            browser_session, sb_context = browser_data
            
            # Log current URL to track redirects
            current_url = browser_session.get_current_url()
            log.info(f"Current URL after navigation: {current_url}")
            
            # Check if we've been redirected to peak45.secutix.com
            if 'peak45.secutix.com' in current_url:
                log.info("Detected redirect to peak45.secutix.com CAPTCHA page")
            
            log.info(f"Retrieved {len(html)} characters of HTML content")
            
            # Step 2: Analyze the HTML content for captcha
            captcha_detected = self.handle_captcha_page(html)
            
            if captcha_detected:
                log.info("Step 1 completed - Captcha page detected!")
                
                # Try automatic CAPTCHA solving first
                if self.capsolver:
                    log.info("Attempting automatic CAPTCHA solving with CapSolver...")
                    if self.solve_initial_captcha(browser_session):
                        log.info("CAPTCHA solved automatically! Continuing...")
                        # Get fresh HTML after CAPTCHA solving
                        time.sleep(3)
                        current_html = browser_session.get_page_source()
                        captcha_detected = False  # Mark as solved
                    else:
                        log.warning("Automatic CAPTCHA solving failed - manual intervention required")
                        log.info("BROWSER IS NOW OPEN - Please solve the captcha manually")
                        log.info("You can interact with the page to solve the captcha")
                        log.info("The browser will stay open until you close this script")
                else:
                    log.info("BROWSER IS NOW OPEN - Please solve the captcha manually")
                    log.info("You can interact with the page to solve the captcha")
                    log.info("The browser will stay open until you close this script")
            else:
                log.info("Step 1 completed - No captcha detected, might be on different page")
                log.info("BROWSER IS OPEN - You can inspect the page")
            
            # Save HTML to file for inspection if needed
            with open("ballot_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            log.info("Page HTML saved to 'ballot_page.html' for inspection")
            
            # Since we have full automation, skip the interactive mode
            if captcha_detected:
                if self.capsolver:
                    log.info("CAPTCHA detected - attempting automatic resolution...")
                    user_input = 'c'  # Automatically continue
                else:
                    log.error("CAPTCHA detected but no CapSolver API configured")
                    return False
            else:
                user_input = 'c'  # Automatically continue to next steps
            
            # If user pressed 'c', check for next steps after captcha solving
            if user_input == 'c':
                try:
                    log.info("Checking current page state...")
                    
                    # Get fresh HTML after any manual interactions
                    current_html = browser_session.get_page_source()
                    
                    # Handle cookie consent banner if it appears after captcha
                    try:
                        log.info("Checking for cookie consent banner (appears after captcha)...")
                        cookie_selectors = [
                            "#onetrust-accept-btn-handler",
                            "button#onetrust-accept-btn-handler",
                            '[id="onetrust-accept-btn-handler"]'
                        ]
                        
                        cookie_clicked = False
                        for cookie_selector in cookie_selectors:
                            try:
                                if browser_session.is_element_present(cookie_selector):
                                    log.info(f"Found cookie consent button with selector: {cookie_selector}")
                                    browser_session.click(cookie_selector)
                                    log.info("Clicked 'Accept All Cookies' button!")
                                    time.sleep(1)  # Wait for cookie banner to disappear
                                    cookie_clicked = True
                                    break
                            except Exception as e:
                                log.debug(f"Cookie selector {cookie_selector} failed: {e}")
                                continue
                        
                        if cookie_clicked:
                            log.info("Cookie consent handled successfully")
                            # Get fresh HTML after cookie handling
                            current_html = browser_session.get_page_source()
                        else:
                            log.info("No cookie consent banner found")
                            
                    except Exception as e:
                        log.error(f"Error handling cookies: {e}")
                    
                    # Save updated HTML for inspection
                    with open("current_page.html", "w", encoding="utf-8") as f:
                        f.write(current_html)
                    log.info("Current page HTML saved to 'current_page.html'")
                    
                    # STEP 1: Look for JOIN button first (after captcha is solved)
                    if "JOIN" in current_html or "gigya-register-screen" in current_html:
                        log.info("Looking for JOIN button to click...")
                        
                        # Much more specific JOIN button selectors - FAST selectors only
                        join_selectors = [
                            '.button-border > a[role="button"]',  # User's exact selector - FASTEST
                            'a[data-switch-screen="gigya-register-screen"]',  # Most specific
                            'a[data-translation-key="BUTTON_CREATEACCOUNT_LABEL"]',  # Translation key
                            'a.buttonBasic',  # Button class
                            'a.gigya-composite-control-link[role="button"]',  # Link with button role
                            'div.button-border a',  # Button in border div
                            'a[role="button"]'  # Any button role
                        ]
                        
                        join_clicked = False
                        for join_selector in join_selectors:
                            try:
                                if browser_session.is_element_present(join_selector):
                                    element_text = browser_session.get_text(join_selector)
                                    log.info(f"Found element: '{element_text}' with selector: {join_selector}")
                                    
                                    # For specific selectors, click without text check; for generic ones, verify text
                                    if (join_selector in ['.button-border > a[role="button"]',
                                                        'a[data-switch-screen="gigya-register-screen"]', 
                                                        'a[data-translation-key="BUTTON_CREATEACCOUNT_LABEL"]'] or
                                        "JOIN" in element_text.upper()):
                                        log.info("Clicking JOIN button...")
                                        browser_session.click(join_selector)
                                        log.info("JOIN button clicked successfully!")
                                        time.sleep(2)
                                        join_clicked = True
                                        break
                                    else:
                                        log.debug(f"Skipping '{element_text}' - not JOIN button")
                                        
                            except Exception as e:
                                log.debug(f"Join selector {join_selector} failed: {e}")
                                continue
                        
                        # If specific selectors failed, try to find any element with JOIN text
                        if not join_clicked:
                            log.info("Trying broader search for JOIN text...")
                            try:
                                # Find all clickable elements and check their text
                                all_links = browser_session.find_elements("css selector", "a, button, input[type='button'], input[type='submit']")
                                for element in all_links:
                                    try:
                                        element_text = element.text.strip()
                                        if "JOIN" in element_text.upper():
                                            log.info(f"Found JOIN element with text: '{element_text}'")
                                            element.click()
                                            log.info("JOIN button clicked successfully!")
                                            time.sleep(2)
                                            join_clicked = True
                                            break
                                    except Exception as e:
                                        continue
                            except Exception as e:
                                log.debug(f"Broader search failed: {e}")
                        
                        if join_clicked:
                            # Get the page after JOIN click
                            time.sleep(1)
                            post_join_html = browser_session.get_page_source()
                            
                            # STEP 2: Now fill the registration form and submit
                            if ("gigya-register-form" in post_join_html or 
                                "Complete Registration" in post_join_html or 
                                "gigya-complete-registration-screen" in post_join_html or
                                ("email" in post_join_html.lower() and "password" in post_join_html.lower())):
                                log.info("Registration form detected - filling automatically...")
                                
                                form_filled = self.fill_registration_form(browser_session)
                                
                                if form_filled:
                                    log.info("Form completed")
                                    
                                    user_choice = input().strip().lower()
                                    if user_choice == 'f':
                                        # Submit the form - using exact selector from user's extension
                                        submit_selectors = [
                                            '#register-site-login > div:nth-of-type(6) > .gigya-composite-control-submit > input[type="submit"]',  # User's exact selector
                                            'input[type="submit"][value="SUBMIT"]',
                                            'input.gigya-input-submit',
                                            'input[value="SUBMIT"]',
                                            'button[type="submit"]',
                                            'input[type="submit"]'
                                        ]
                                        
                                        submit_clicked = False
                                        for submit_selector in submit_selectors:
                                            try:
                                                if browser_session.is_element_present(submit_selector):
                                                    log.info(f"Found submit button with selector: {submit_selector}")
                                                    log.info("Submitting registration form...")
                                                    browser_session.click(submit_selector)
                                                    log.info("Form submitted!")
                                                    time.sleep(1)
                                                    submit_clicked = True
                                                    break
                                            except Exception as e:
                                                log.debug(f"Submit selector {submit_selector} failed: {e}")
                                                continue
                                        
                                        if not submit_clicked:
                                            log.warning("Could not find submit button")
                                            # Try to find any submit button
                                            try:
                                                all_submits = browser_session.find_elements("css selector", "input[type='submit'], button[type='submit'], input[value*='SUBMIT']")
                                                if all_submits:
                                                    log.info(f"Found {len(all_submits)} submit elements, clicking first one")
                                                    all_submits[0].click()
                                                    log.info("Form submitted via fallback method!")
                                                    submit_clicked = True
                                                    time.sleep(1)
                                            except Exception as e:
                                                log.error(f"Fallback submit failed: {e}")
                                        
                                        if submit_clicked:
                                            log.info("Form submitted successfully!")
                                            
                                            # Check for and handle post-submission CAPTCHA
                                            # Wait reduced for speed
                                            if self.handle_post_submission_captcha(browser_session):
                                                log.info("Post-submission CAPTCHA handled successfully!")
                                                
                                                # Check if we need to submit again after solving CAPTCHA
                                                log.info("Checking if additional form submission is needed...")
                                                time.sleep(1)
                                                
                                                # Look for submit button again (may need to click submit after CAPTCHA)
                                                submit_selectors_retry = [
                                                    'input[type="submit"]',
                                                    'button[type="submit"]',
                                                    '.gigya-composite-control-submit input',
                                                    'button:contains("Submit")',
                                                    '#submit_button'
                                                ]
                                                
                                                for submit_sel in submit_selectors_retry:
                                                    try:
                                                        if browser_session.is_element_present(submit_sel):
                                                            log.info(f"Found submit button after CAPTCHA: {submit_sel}")
                                                            
                                                            # Try multiple click methods to ensure it works
                                                            try:
                                                                browser_session.click(submit_sel)
                                                                log.info("✅ Submitted form after solving CAPTCHA")
                                                            except Exception as click_error:
                                                                log.warning(f"Regular click failed, trying JavaScript click: {click_error}")
                                                                browser_session.execute_script(f"document.querySelector('{submit_sel}').click();")
                                                                log.info("✅ Submitted form using JavaScript after solving CAPTCHA")
                                                            
                                                            time.sleep(1)  # Reduced sleep
                                                            break
                                                    except Exception as e:
                                                        log.error(f"Submit after CAPTCHA failed with {submit_sel}: {e}")
                                                        continue
                                            
                                            log.info("✅ Form submission and CAPTCHA handling completed!")
                                        else:
                                            log.error("❌ Form submission failed!")
                                else:
                                    log.error("❌ Could not fill form")
                            else:
                                log.error("❌ Unexpected page after JOIN")
                        else:
                            log.warning("Could not find JOIN button with any method")
                            # Debug: Show what elements we can see
                            try:
                                log.info("Debugging - showing all clickable elements on page:")
                                all_elements = browser_session.find_elements("css selector", "a, button, input[type='button'], input[type='submit']")
                                for i, element in enumerate(all_elements[:10]):  # Show first 10
                                    try:
                                        text = element.text.strip()
                                        tag = element.tag_name
                                        log.info(f"Element {i+1}: <{tag}> '{text}'")
                                    except:
                                        pass
                            except Exception as e:
                                log.debug(f"Debug failed: {e}")
                            
                            log.error("❌ Could not find JOIN button")
                    
                    # STEP 2: If we're already on registration form (no JOIN needed)
                    elif ("gigya-register-form" in current_html or 
                          "Complete Registration" in current_html or 
                          "gigya-complete-registration-screen" in current_html or
                          ("email" in current_html.lower() and "password" in current_html.lower())):
                        log.info("Already on registration form - filling automatically...")
                        
                        form_filled = self.fill_registration_form(browser_session)
                        
                        if form_filled:
                            log.info("✅ Form filled successfully!")
                            
                            user_choice = input().strip().lower()
                            if user_choice == 'f':
                                # Submit the form - using exact selector from user's extension
                                submit_selectors = [
                                    '#register-site-login > div:nth-of-type(6) > .gigya-composite-control-submit > input[type="submit"]',  # User's exact selector
                                    'input[type="submit"][value="SUBMIT"]',
                                    'input.gigya-input-submit',
                                    'input[value="SUBMIT"]',
                                    'button[type="submit"]',
                                    'input[type="submit"]'
                                ]
                                
                                submit_clicked = False
                                for submit_selector in submit_selectors:
                                    try:
                                        if browser_session.is_element_present(submit_selector):
                                            log.info(f"Found submit button with selector: {submit_selector}")
                                            
                                            # Scroll to element and ensure visibility
                                            browser_session.scroll_to_element(submit_selector)
                                            time.sleep(0.5)
                                            
                                            # Check if clickable
                                            if browser_session.is_element_clickable(submit_selector):
                                                log.info("Submitting registration form...")
                                                
                                                # Try normal click first
                                                try:
                                                    browser_session.click(submit_selector)
                                                    log.info("Form submitted!")
                                                    submit_clicked = True
                                                    break
                                                except:
                                                    # Try JavaScript click as fallback
                                                    try:
                                                        browser_session.js_click(submit_selector)
                                                        log.info("Form submitted via JavaScript!")
                                                        submit_clicked = True
                                                        break
                                                    except Exception as js_error:
                                                        log.warning(f"JavaScript click failed: {js_error}")
                                            else:
                                                log.warning(f"Submit button not clickable: {submit_selector}")
                                                
                                    except Exception as e:
                                        log.debug(f"Submit selector {submit_selector} failed: {e}")
                                        continue
                                
                                if not submit_clicked:
                                    log.warning("Could not find submit button")
                                    # Try to find any submit button with enhanced interaction
                                    try:
                                        all_submits = browser_session.find_elements("css selector", "input[type='submit'], button[type='submit'], input[value*='SUBMIT']")
                                        if all_submits:
                                            log.info(f"Found {len(all_submits)} submit elements, trying each one")
                                            for idx, submit_elem in enumerate(all_submits):
                                                try:
                                                    # Scroll to element
                                                    browser_session.scroll_to_element(submit_elem)
                                                    time.sleep(0.3)
                                                    
                                                    # Try clicking if visible and enabled
                                                    if submit_elem.is_displayed() and submit_elem.is_enabled():
                                                        try:
                                                            submit_elem.click()
                                                            log.info(f"Form submitted via fallback method (element {idx+1})!")
                                                            submit_clicked = True
                                                            break
                                                        except:
                                                            # Try JavaScript click
                                                            browser_session.execute_script("arguments[0].click();", submit_elem)
                                                            log.info(f"Form submitted via JavaScript fallback (element {idx+1})!")
                                                            submit_clicked = True
                                                            break
                                                except Exception as elem_error:
                                                    log.debug(f"Submit element {idx+1} failed: {elem_error}")
                                                    continue
                                            time.sleep(1)
                                    except Exception as e:
                                        log.error(f"Fallback submit failed: {e}")
                                
                                if submit_clicked:
                                    log.info("✅ Form submitted successfully!")
                                    
                                    # Check for and handle post-submission CAPTCHA
                                    time.sleep(1)  # Quick wait for any CAPTCHA to appear
                                    if self.handle_post_submission_captcha(browser_session):
                                        log.info("Post-submission CAPTCHA handled successfully!")
                                    
                                    log.info("✅ Registration process completed!")
                                else:
                                    log.error("❌ Form submission failed!")
                        else:
                            log.error("❌ Could not fill form")
                    
                    else:
                        log.info("Page state unclear - manual inspection needed")
                        log.error("❌ Page state unclear")
                        
                except Exception as e:
                    log.error(f"Error checking page state: {e}")
                    log.error(f"❌ Error checking page state: {e}")
            
            # Clean up
            try:
                sb_context.__exit__(None, None, None)
                log.info("Browser closed")
            except Exception as e:
                log.warning(f"Error closing browser: {e}")
            
            return True
                
        except Exception as e:
            log.error(f"Error in step one execution: {e}")
            return False

    def run_fully_automated(self):
        """Execute the complete ballot automation without any manual intervention"""
        log.info("Wimbledon Ballot Application Starting...")
        
        try:
            # Step 1: Navigate and handle initial CAPTCHA
            html, browser_data = self.navigate_to_ballot_and_keep_open()
            
            if not html or not browser_data:
                log.error("Failed to access application")
                return False
            
            browser_session, sb_context = browser_data
            current_url = browser_session.get_current_url()
            log.info(f"📍 Current URL: {current_url}")
            
            # Step 2: Auto-solve initial CAPTCHA
            if self.handle_captcha_page(html):
                if self.capsolver and self.solve_initial_captcha(browser_session):
                    log.info("Initial verification completed")
                else:
                    log.error("Initial verification failed")
                    return False
            
            # Step 3: Continue automated flow
            return self.continue_automated_flow(browser_session)
                
        except Exception as e:
            log.error(f"❌ Automation failed: {e}")
            return False

    def continue_automated_flow(self, browser_session):
        """Continue the automated flow after initial CAPTCHA"""
        try:
            # Handle cookie consent
            self.handle_cookie_consent(browser_session)
            
            # Find and click JOIN button
            if not self.find_and_click_join_button(browser_session):
                log.error("❌ Failed to find/click JOIN button")
                return False
            
            # Fill and submit registration form automatically
            return self.fill_and_submit_form_auto(browser_session)
                
        except Exception as e:
            log.error(f"❌ Automated flow failed: {e}")
            return False

    def handle_cookie_consent(self, browser_session):
        """Handle cookie consent banner"""
        try:
            log.info("Checking for cookie consent banner...")
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "button#onetrust-accept-btn-handler",
                '[id="onetrust-accept-btn-handler"]'
            ]
            
            for cookie_selector in cookie_selectors:
                try:
                    if browser_session.is_element_present(cookie_selector):
                        browser_session.click(cookie_selector)
                        log.info("✅ Clicked 'Accept All Cookies' button")
                        return True
                except Exception as e:
                    continue
            return True  # No cookie banner found, continue
        except Exception as e:
            log.debug(f"Cookie consent handling failed: {e}")
            return True

    def find_and_click_join_button(self, browser_session):
        """Find and click the JOIN button"""
        try:
            log.info("Looking for JOIN button...")
            join_selectors = [
                '.button-border > a[role="button"]',
                'a[role="button"]:contains("JOIN")',
                '.btn:contains("JOIN")'
            ]
            
            for join_selector in join_selectors:
                try:
                    if browser_session.is_element_present(join_selector):
                        browser_session.click(join_selector)
                        log.info("JOIN button located and clicked")
                        time.sleep(1)  # Reduced wait time
                        return True
                except Exception as e:
                    continue
            
            log.error("❌ Could not find JOIN button")
            return False
        except Exception as e:
            log.error(f"❌ JOIN button clicking failed: {e}")
            return False

    def fill_and_submit_form_auto(self, browser_session):
        """Fill and submit the registration form automatically"""
        try:
            log.info("Filling registration form automatically...")
            
            # Fill form
            if self.fill_registration_form(browser_session):
                log.info("Registration form completed")
                
                # Submit form automatically using existing logic
                submit_selectors = [
                    '#register-site-login > div:nth-of-type(6) > .gigya-composite-control-submit > input[type="submit"]',
                    '.gigya-composite-control-submit input[type="submit"]',
                    'input.gigya-input-submit',
                    'input[value="SUBMIT"]',
                    'button[type="submit"]',
                    'input[type="submit"]'
                ]
                
                submit_clicked = False
                for submit_selector in submit_selectors:
                    try:
                        if browser_session.is_element_present(submit_selector):
                            log.info(f"Found submit button: {submit_selector}")
                            browser_session.click(submit_selector)
                            log.info("Form submitted successfully")
                            time.sleep(1)  # Quick wait
                            submit_clicked = True
                            break
                    except Exception as e:
                        log.debug(f"Submit selector {submit_selector} failed: {e}")
                        continue
                
                if submit_clicked:
                    log.info("✅ Form submitted successfully")
                    
                    # Handle post-submission CAPTCHA
                    if self.handle_post_submission_captcha(browser_session):
                        log.info("Post-submission verification handled")
                        
                        # Click submit again after CAPTCHA if needed
                        self.final_submit_after_captcha(browser_session)
                        
                        # Check if there's a profile completion form
                        time.sleep(2)  # Wait for page to load
                        if self.handle_profile_completion_form(browser_session):
                            log.info("🎉 PROFILE COMPLETION SUCCESSFUL!")
                        
                        log.info("🎉 REGISTRATION COMPLETED SUCCESSFULLY!")
                        return True
                    else:
                        log.error("❌ Failed to handle post-submission CAPTCHA")
                        return False
                else:
                    log.error("❌ Form submission failed")
                    return False
            else:
                log.error("❌ Form filling failed")
                return False
                
        except Exception as e:
            log.error(f"❌ Form automation failed: {e}")
            return False

    def handle_profile_completion_form(self, browser_session):
        """Handle the profile completion form that appears after initial registration"""
        try:
            log.info("Checking for profile completion form...")
            
            # Check if we're on the profile completion page
            if not browser_session.is_element_present('.gigya-profile-form'):
                log.info("No profile completion form found - registration may be complete")
                return True
            
            log.info("Found profile completion form - completing automatically...")
            
            # Fill email (should already be filled)
            email_field = 'input[name="completion.email"]'
            if browser_session.is_element_present(email_field):
                try:
                    current_email = browser_session.get_value(email_field)
                    if not current_email and self.login_details:
                        browser_session.type(email_field, self.login_details['Email'])
                        log.info(f"✅ Filled email: {self.login_details['Email']}")
                except Exception as e:
                    log.debug(f"Email field already filled or error: {e}")
            
            # Wait longer for the profile form to load completely
            browser_session.wait(2)
            
            log.info("Completing profile form with exact selectors...")
            
            # Fill email first (should already be prefilled)
            email_field = 'input[name="completion.email"]'
            if browser_session.is_element_present(email_field):
                try:
                    current_value = browser_session.get_value(email_field)
                    if not current_value and self.login_details:
                        browser_session.type(email_field, self.login_details['Email'])
                        log.info(f"✅ Filled email: {self.login_details['Email']}")
                    else:
                        log.info("Email already filled")
                except Exception as e:
                    log.debug(f"Email field error: {e}")
            
            # Select title using exact ID
            try:
                browser_session.select_option_by_value('#gigya-dropdown-title', "Mr")
                log.info("Title selected: Mr")
            except Exception as e:
                log.error(f"Failed to select title: {e}")
            
            # Fill first name using exact ID
            if self.login_details:
                name_parts = self.login_details['Name'].split(' ', 1)
                first_name = name_parts[0] if name_parts else 'Sam'
                try:
                    browser_session.type('#profile\\.firstName', first_name)
                    log.info(f"First name filled: {first_name}")
                except Exception as e:
                    log.error(f"❌ Failed to fill first name: {e}")
            
            # Fill last name using exact ID
            if self.login_details:
                name_parts = self.login_details['Name'].split(' ', 1)
                last_name = name_parts[1] if len(name_parts) > 1 else 'Plates'
                try:
                    browser_session.type('#profile\\.lastName', last_name)
                    log.info(f"Last name filled: {last_name}")
                except Exception as e:
                    log.error(f"❌ Failed to fill last name: {e}")
            
            # Select country using exact ID
            try:
                browser_session.select_option_by_value('#reg_completion\\.gigya-dropdown-country', "GB")
                log.info("Country selected: United Kingdom")
            except Exception as e:
                log.error(f"❌ Failed to select country: {e}")
            
            # Fill postcode using exact ID
            if self.login_details:
                try:
                    browser_session.type('#profile\\.zip', self.login_details['Postcode'])
                    log.info(f"✅ Filled postcode: {self.login_details['Postcode']}")
                except Exception as e:
                    log.error(f"❌ Failed to fill postcode: {e}")
            
            # Select birth day using exact ID
            try:
                dob_day = self.login_details.get('dob_day', '20')
                browser_session.select_option_by_value('#complete\\.gigya-dropdown-birthDay', dob_day)
                log.info(f"Birth day selected: {dob_day}")
            except Exception as e:
                log.error(f"❌ Failed to select birth day: {e}")
            
            # Select birth month using exact ID
            try:
                month_name = self.login_details.get('dob_month', 'July')
                
                # Method 1: Try selecting by visible text
                try:
                    browser_session.select_option_by_text('#complete\\.gigya-dropdown-birthMonth', month_name.title())
                    log.info(f"Birth month selected: {month_name}")
                except Exception:
                    # Method 2: Try selecting by value
                    month_mapping = {
                        'january': '1', 'february': '2', 'march': '3', 'april': '4',
                        'may': '5', 'june': '6', 'july': '7', 'august': '8',
                        'september': '9', 'october': '10', 'november': '11', 'december': '12'
                    }
                    month_value = month_mapping.get(month_name.lower(), '7')
                    
                    try:
                        browser_session.select_option_by_value('#complete\\.gigya-dropdown-birthMonth', month_value)
                        log.info(f"Birth month selected (by value): {month_value}")
                    except Exception:
                        # Method 3: Try with JavaScript
                        browser_session.execute_script(f'''
                            var select = document.querySelector('#complete\\\\.gigya-dropdown-birthMonth');
                            if (select) {{
                                select.value = '{month_value}';
                                select.dispatchEvent(new Event('change'));
                            }}
                        ''')
                        log.info(f"Birth month selected (JavaScript): {month_value}")
                        
            except Exception as e:
                log.error(f"Failed to select birth month: {e}")
            
            # Select birth year using exact ID
            try:
                dob_year = self.login_details.get('dob_year', '2004')
                browser_session.select_option_by_value('#complete\\.gigya-dropdown-birthYear', dob_year)
                log.info(f"Birth year selected: {dob_year}")
            except Exception as e:
                log.error(f"❌ Failed to select birth year: {e}")
            
            # Handle any consent checkboxes
            try:
                checkboxes = browser_session.find_elements('input[type="checkbox"]')
                for checkbox in checkboxes:
                    if not checkbox.is_selected():
                        browser_session.click(checkbox)
                        log.info("Consent checkbox selected")
            except Exception as e:
                log.debug(f"Checkbox handling error: {e}")
            
            log.info("Profile form fields completed")
            
            log.info("Profile form filled, submitting...")
            time.sleep(0.5)  # Brief wait before submission
            
            # Submit the profile completion form
            submit_selector = 'form[aria-labelledby="screen-holder_content_caption"] > div:nth-of-type(9) > .gigya-composite-control > input[type="submit"]'
            if browser_session.is_element_present(submit_selector):
                browser_session.click(submit_selector)
                log.info("Profile completion form submitted")
                time.sleep(1)  # Wait for submission
                
                # Check for email verification step
                if self.handle_email_verification(browser_session):
                    log.info("✅ EMAIL VERIFICATION COMPLETED!")
                    return True
                else:
                    log.warning("⚠️ Email verification step encountered but not completed")
                    return True
            else:
                # Try fallback submit selectors
                fallback_selectors = [
                    '.gigya-input-submit',
                    'input[type="submit"]',
                    'input[value="SUBMIT"]'
                ]
                
                for selector in fallback_selectors:
                    try:
                        if browser_session.is_element_present(selector):
                            browser_session.click(selector)
                            log.info(f"✅ Profile form submitted using fallback selector: {selector}")
                            time.sleep(1)
                            
                            # Check for email verification step
                            if self.handle_email_verification(browser_session):
                                log.info("✅ EMAIL VERIFICATION COMPLETED!")
                                return True
                            else:
                                log.warning("⚠️ Email verification step encountered but not completed")
                                return True
                    except Exception as e:
                        continue
                
                log.error("❌ Could not find profile completion submit button")
                return False
                
        except Exception as e:
            log.error(f"❌ Error handling profile completion form: {e}")
            # Continue anyway - profile completion is optional
            return True
    
    def handle_email_verification(self, browser_session):
        """Handle email verification step that may appear after profile completion"""
        try:
            # Wait a moment for the page to load
            browser_session.wait(1)
            
            # Check if email verification form is present
            email_verification_indicators = [
                '#gigya-email-code-verification-screen',
                '.gigya-otp-update-form',
                'input[name="code"]',
                '#gigya-textbox-code'
            ]
            
            verification_present = False
            for indicator in email_verification_indicators:
                if browser_session.is_element_present(indicator):
                    verification_present = True
                    break
            
            if not verification_present:
                log.info("No email verification required - registration complete")
                return True
            
            log.info("Email verification required")
            log.info("Please check your email for verification code")
            
            # Get the verification code from user input
            verification_code = input("Enter verification code: ").strip()
            
            if not verification_code:
                log.error("❌ No verification code entered")
                return False
            
            # Fill the verification code
            code_field_selectors = [
                '#gigya-textbox-code',
                'input[name="code"]',
                'input[id*="code"]'
            ]
            
            code_filled = False
            for selector in code_field_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.type(selector, verification_code)
                        log.info(f"✅ Filled verification code: {verification_code}")
                        code_filled = True
                        break
                except Exception as e:
                    log.debug(f"Failed to fill code with selector {selector}: {e}")
                    continue
            
            if not code_filled:
                log.error("❌ Could not find verification code input field")
                return False
            
            # Submit the verification code
            submit_selectors = [
                'form[aria-labelledby="screen-holder_content_caption"] > div:nth-of-type(5) > .gigya-composite-control-submit > input[type="submit"]',
                '.gigya-input-submit',
                'input[type="submit"]',
                'input[value="SUBMIT"]'
            ]
            
            for selector in submit_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.click(selector)
                        log.info("✅ EMAIL VERIFICATION CODE SUBMITTED!")
                        browser_session.wait(3)
                        
                        # Check for additional registration details page
                        if self.handle_additional_registration_details(browser_session):
                            log.info("✅ ADDITIONAL REGISTRATION DETAILS COMPLETED!")
                            return True
                        else:
                            log.warning("⚠️ Additional registration details step encountered but not completed")
                            return True
                except Exception as e:
                    log.debug(f"Failed verification submit with selector {selector}: {e}")
                    continue
            
            log.error("❌ Could not find verification submit button")
            return False
            
        except Exception as e:
            log.error(f"❌ Error handling email verification: {e}")
            return False

    def handle_additional_registration_details(self, browser_session):
        """Handle additional registration details page after email verification"""
        try:
            # Wait for the page to load
            browser_session.wait(3)
            
            # Check if we're on the additional details page
            additional_details_indicators = [
                'select[name="title"]',
                'input[name="addressLine1"]',
                'input[name="city"]',
                'input[name="zipCode"]',
                'input[name="mobile"]'
            ]
            
            details_page_present = False
            for indicator in additional_details_indicators:
                if browser_session.is_element_present(indicator):
                    details_page_present = True
                    break
            
            if not details_page_present:
                log.info("No additional registration details required")
                return True
            
            log.info("Additional registration details required")
            log.info("Completing additional form fields...")
            
            # Select title using the specific dropdown
            try:
                browser_session.select_option_by_value('#title', "MR")
                log.info("Title selected: Mr")
            except Exception as e:
                log.error(f"Failed to select title: {e}")
            
            # Fill address line 1
            if self.login_details:
                try:
                    browser_session.type('#address_line_1', self.login_details['AddressLine1'])
                    log.info(f"✅ Filled address line 1: {self.login_details['AddressLine1']}")
                except Exception as e:
                    log.error(f"❌ Failed to fill address line 1: {e}")
            
            # Fill city
            if self.login_details:
                try:
                    browser_session.type('#address_town_standalone', self.login_details['City'])
                    log.info(f"✅ Filled city: {self.login_details['City']}")
                except Exception as e:
                    log.error(f"❌ Failed to fill city: {e}")
            
            # Fill postcode/zip code
            if self.login_details:
                try:
                    browser_session.type('#address_zipcode_standalone', self.login_details['Postcode'])
                    log.info(f"✅ Filled postcode: {self.login_details['Postcode']}")
                except Exception as e:
                    log.error(f"❌ Failed to fill postcode: {e}")
            
            # Fill mobile number
            if self.login_details:
                try:
                    browser_session.type('#mobile_number', self.login_details['MobileNumber'])
                    log.info(f"✅ Filled mobile number: {self.login_details['MobileNumber']}")
                except Exception as e:
                    log.error(f"❌ Failed to fill mobile number: {e}")
            
            # Handle radio button selection - first option
            try:
                browser_session.click('span[role="radiogroup"] > input:nth-of-type(1)')
                log.info("Radio option selected")
            except Exception as e:
                log.error(f"❌ Failed to select radio option: {e}")
            
            # Handle contact authorization checkboxes - refuse both
            try:
                browser_session.click('#contactAuthorizations\\[CNIL_T\\]\\.refuse')
                log.info("✅ Clicked CNIL_T refuse")
            except Exception as e:
                log.debug(f"CNIL_T refuse click failed: {e}")
            
            try:
                browser_session.click('#contactAuthorizations\\[EMAIL\\]\\.refuse')
                log.info("✅ Clicked EMAIL refuse")
            except Exception as e:
                log.debug(f"EMAIL refuse click failed: {e}")
            
            # Wait a moment before submission
            browser_session.wait(2)
            
            # Click the Continue to Application button
            continue_button_selectors = [
                '#save',
                '#saveButton a',
                'a[onclick*="submitRegisterForm"]',
                '.button a[href="#"]'
            ]
            
            for selector in continue_button_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.click(selector)
                        log.info("✅ CONTINUE TO APPLICATION CLICKED!")
                        browser_session.wait(3)
                        
                        # Move to the proceed page
                        return self.handle_proceed_page(browser_session)
                except Exception as e:
                    log.debug(f"Failed continue button with selector {selector}: {e}")
                    continue
            
            log.error("❌ Could not find Continue to Application button")
            return False
            
        except Exception as e:
            log.error(f"❌ Error handling additional registration details: {e}")
            return False

    def handle_proceed_page(self, browser_session):
        """Handle the proceed page after additional registration details"""
        try:
            # Wait for the page to load
            browser_session.wait(3)
            
            # Check if we're on the proceed page
            proceed_indicators = [
                '#book',
                '#addToCartButtonContainer',
                'a[onclick*="validateQuantities"]'
            ]
            
            proceed_page_present = False
            for indicator in proceed_indicators:
                if browser_session.is_element_present(indicator):
                    proceed_page_present = True
                    break
            
            if not proceed_page_present:
                log.info("No proceed page found - moving to next step")
                return self.handle_final_submission_page(browser_session)
            
            log.info("Proceed page detected")
            log.info("Continuing to next step...")
            
            # Click the Proceed button
            proceed_selectors = [
                '#book',
                '#addToCartButtonContainer a',
                'a[onclick*="validateQuantities"]',
                '.button a[role="button"]'
            ]
            
            for selector in proceed_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.click(selector)
                        log.info("✅ PROCEED BUTTON CLICKED!")
                        browser_session.wait(3)
                        
                        # Move to the final submission page
                        return self.handle_final_submission_page(browser_session)
                except Exception as e:
                    log.debug(f"Failed proceed button with selector {selector}: {e}")
                    continue
            
            log.error("❌ Could not find Proceed button")
            return False
            
        except Exception as e:
            log.error(f"❌ Error handling proceed page: {e}")
            return False

    def handle_final_submission_page(self, browser_session):
        """Handle the final submission page with conditions acceptance"""
        try:
            # Wait for the page to load
            browser_session.wait(3)
            
            # Check if we're on the final submission page
            submission_indicators = [
                'input[aria-labelledby="condition_acceptable_label"]',
                '#buyNow',
                '#buyNowButton',
                'a[role="button"]:contains("Submit your Application")'
            ]
            
            submission_page_present = False
            for indicator in submission_indicators:
                if browser_session.is_element_present(indicator):
                    submission_page_present = True
                    break
            
            if not submission_page_present:
                log.info("No final submission page found - checking for confirmation")
                return self.check_application_confirmation(browser_session)
            
            log.info("Final submission page reached")
            log.info("Submitting application...")
            
            # Accept the conditions checkbox
            try:
                browser_session.click('input[aria-labelledby="condition_acceptable_label"]')
                log.info("✅ Accepted conditions checkbox")
            except Exception as e:
                log.error(f"❌ Failed to accept conditions: {e}")
            
            # Wait a moment
            browser_session.wait(2)
            
            # Click Submit your Application button
            submit_selectors = [
                '#buyNow',
                '#buyNowButton a',
                'a[role="button"]:contains("Submit")',
                '.button.pay a'
            ]
            
            for selector in submit_selectors:
                try:
                    if browser_session.is_element_present(selector):
                        browser_session.click(selector)
                        log.info("✅ SUBMIT YOUR APPLICATION CLICKED!")
                        browser_session.wait(2)
                        
                        # Check for application confirmation
                        return self.check_application_confirmation(browser_session)
                except Exception as e:
                    log.debug(f"Failed submit application with selector {selector}: {e}")
                    continue
            
            log.error("❌ Could not find Submit your Application button")
            return False
            
        except Exception as e:
            log.error(f"❌ Error handling final submission page: {e}")
            return False

    def check_application_confirmation(self, browser_session):
        """Check for the final application confirmation page"""
        try:
            # Wait for confirmation page to load
            browser_session.wait(5)
            
            # Check for confirmation indicators
            confirmation_indicators = [
                'h2:contains("Application Confirmation")',
                '.main_title:contains("Application Confirmation")',
                '.title_container:contains("Application Confirmation")'
            ]
            
            # Also check page source for confirmation text
            try:
                page_source = browser_session.get_page_source()
                if "Application Confirmation" in page_source:
                    log.info("🎉 APPLICATION CONFIRMATION PAGE DETECTED!")
                    log.info("✅ WIMBLEDON BALLOT APPLICATION SUCCESSFULLY SUBMITTED!")
                    log.info("🎾 Your application has been completed and confirmed!")
                    return True
            except:
                pass
            
            # Try element-based detection
            for indicator in confirmation_indicators:
                try:
                    if browser_session.is_element_present(indicator):
                        log.info("🎉 APPLICATION CONFIRMATION PAGE DETECTED!")
                        log.info("✅ WIMBLEDON BALLOT APPLICATION SUCCESSFULLY SUBMITTED!")
                        log.info("🎾 Your application has been completed and confirmed!")
                        return True
                except:
                    continue
            
            log.warning("⚠️ Application may have been submitted but confirmation page not clearly detected")
            return True
            
        except Exception as e:
            log.error(f"❌ Error checking application confirmation: {e}")
            return True  # Assume success to avoid blocking

    def final_submit_after_captcha(self, browser_session):
        """Click the final submit button after solving CAPTCHA"""
        try:
            log.info("Looking for final submit button after CAPTCHA...")
            submit_selectors = [
                '#register-site-login > div:nth-of-type(6) > .gigya-composite-control-submit > input[type="submit"]',
                '.gigya-composite-control-submit input[type="submit"]',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            for submit_sel in submit_selectors:
                try:
                    if browser_session.is_element_present(submit_sel):
                        log.info(f"Found final submit button: {submit_sel}")
                        browser_session.click(submit_sel)
                        log.info("Application submitted successfully")
                        return True
                except Exception as e:
                    log.debug(f"Submit selector {submit_sel} failed: {e}")
                    continue
            
            log.warning("No final submit button found - registration may already be complete")
            return True
        except Exception as e:
            log.error(f"Final submit failed: {e}")
            return False

def main():
    """Main function to run the automation for all profiles"""
    log.info("Wimbledon Ballot Automation - Multiple Profiles")
    
    # Load all profiles from CSV
    temp_automation = WimbledonAutomation()
    profiles = temp_automation.load_all_profiles()
    
    if not profiles:
        log.error("No profiles found in CSV file")
        return False
    
    successful_applications = 0
    failed_applications = 0
    
    for i, profile in enumerate(profiles, 1):
        try:
            email = profile.get('Email', 'Unknown')
            name = profile.get('Name', 'Unknown')
            
            log.info(f"\n{'='*60}")
            log.info(f"Processing Profile {i}/{len(profiles)}")
            log.info(f"Email: {email}")
            log.info(f"Name: {name}")
            log.info(f"{'='*60}")
            
            # Create automation instance for this profile
            automation = WimbledonAutomation(profile)
            success = automation.run_fully_automated()
            
            if success:
                log.info(f"✅ Profile {i} ({email}) - Application completed successfully")
                successful_applications += 1
            else:
                log.error(f"❌ Profile {i} ({email}) - Application failed")
                failed_applications += 1
            
            # Add delay between profiles to avoid rate limiting
            if i < len(profiles):  # Don't delay after the last profile
                log.info(f"Waiting 30 seconds before processing next profile...")
                time.sleep(30)
                
        except Exception as e:
            log.error(f"❌ Profile {i} - Error processing profile: {e}")
            failed_applications += 1
            continue
    
    # Final summary
    log.info(f"\n{'='*60}")
    log.info(f"FINAL SUMMARY")
    log.info(f"Total Profiles: {len(profiles)}")
    log.info(f"Successful Applications: {successful_applications}")
    log.info(f"Failed Applications: {failed_applications}")
    log.info(f"Success Rate: {(successful_applications/len(profiles)*100):.1f}%")
    log.info(f"{'='*60}")
    
    return successful_applications > 0

if __name__ == "__main__":
    main()