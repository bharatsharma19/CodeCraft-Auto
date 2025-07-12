import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
import os
from config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
    LEETCODE_USERNAME,
    LEETCODE_PASSWORD,
    check_leetcode_config,
)
import logging


class SubmissionManager:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.is_logged_in = False

    def setup_driver(self):
        """Setup Chrome driver with enhanced error handling and Cloudflare bypass"""
        try:
            options = webdriver.ChromeOptions()

            # Remove headless mode to bypass Cloudflare detection
            # options.add_argument("--headless")

            # Enhanced options to bypass Cloudflare
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            # options.add_argument("--disable-javascript")  # Remove this as LeetCode needs JS
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            options.add_argument("--window-size=1920,1080")

            # Enhanced user agent to look more like a real browser
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Additional options to bypass Cloudflare
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # Add additional preferences to avoid detection
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.media_stream": 2,
            }
            options.add_experimental_option("prefs", prefs)

            # Try to use existing ChromeDriver first
            try:
                service = Service("chromedriver")
                self.driver = webdriver.Chrome(service=service, options=options)
                print("Chrome driver setup successful (existing)")
            except:
                # Download and use ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("Chrome driver setup successful (downloaded)")

            # Execute script to remove webdriver property
            if self.driver:
                self.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Browser automation will be disabled")
            self.driver = None

    def login_to_leetcode(self):
        """Login to LeetCode with credentials and Cloudflare bypass"""
        if not self.driver:
            return False, "Driver not available"

        if not check_leetcode_config():
            return False, "LeetCode credentials not configured"

        try:
            print("Logging in to LeetCode...")

            # Navigate to LeetCode login page
            self.driver.get("https://leetcode.com/accounts/login/")
            time.sleep(5)  # Increased wait time for Cloudflare

            # Check if we hit Cloudflare protection
            page_source = self.driver.page_source.lower()
            if "cloudflare" in page_source or "checking your browser" in page_source:
                print("Cloudflare protection detected, waiting...")
                time.sleep(10)  # Wait for Cloudflare to clear

                # Refresh page after Cloudflare
                self.driver.refresh()
                time.sleep(5)

            # Wait for login form to load with multiple strategies
            login_form_found = False
            wait_time = 20

            try:
                # Strategy 1: Wait for login form
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.ID, "id_login"))
                )
                login_form_found = True
                print("Login form found")
            except TimeoutException:
                print("Login form not found with ID, trying alternative selectors...")

                # Strategy 2: Try alternative login form selectors
                alternative_form_selectors = [
                    "input[name='login']",
                    "input[type='email']",
                    "input[placeholder*='email']",
                    "input[placeholder*='username']",
                    "input[placeholder*='Email']",
                    "input[placeholder*='Username']",
                ]

                for selector in alternative_form_selectors:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, selector)
                        login_form_found = True
                        print(f"Found login form with selector: {selector}")
                        break
                    except:
                        continue

                if not login_form_found:
                    print("❌ Could not find login form")
                    return False, "Login form not found"

            # Find and fill username field with multiple strategies
            username_entered = False
            username_selectors = [
                (By.ID, "id_login"),
                (By.CSS_SELECTOR, "input[name='login']"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='username']"),
                (By.CSS_SELECTOR, "input[placeholder*='Email']"),
                (By.CSS_SELECTOR, "input[placeholder*='Username']"),
            ]

            for by, selector in username_selectors:
                try:
                    username_field = self.driver.find_element(by, selector)
                    username_field.clear()
                    time.sleep(1)
                    username_field.send_keys(LEETCODE_USERNAME)
                    print("Username entered")
                    username_entered = True
                    break
                except NoSuchElementException:
                    continue

            if not username_entered:
                print("Username field not found")
                return False, "Username field not found"

            # Find and fill password field with multiple strategies
            password_entered = False
            password_selectors = [
                (By.ID, "id_password"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[placeholder*='password']"),
                (By.CSS_SELECTOR, "input[placeholder*='Password']"),
            ]

            for by, selector in password_selectors:
                try:
                    password_field = self.driver.find_element(by, selector)
                    password_field.clear()
                    time.sleep(1)
                    password_field.send_keys(LEETCODE_PASSWORD)
                    print("Password entered")
                    password_entered = True
                    break
                except NoSuchElementException:
                    continue

            if not password_entered:
                print("Password field not found")
                return False, "Password field not found"

            # Check for Cloudflare Turnstile widget
            try:
                turnstile_widget = self.driver.find_element(
                    By.ID, "cf-chl-widget-kxlgh_response"
                )
                logging.warning("Cloudflare Turnstile widget detected")
                logging.info("Waiting for Turnstile to complete...")
                time.sleep(15)  # Wait for Turnstile to process
            except NoSuchElementException:
                # Try alternative Turnstile widget IDs
                turnstile_ids = [
                    "cf-chl-widget-8jhrt_response",  # From your HTML
                    "cf-chl-widget-kxlgh_response",  # Original ID
                    "cf-turnstile-response",
                ]

                turnstile_found = False
                for widget_id in turnstile_ids:
                    try:
                        turnstile_widget = self.driver.find_element(By.ID, widget_id)
                        logging.warning(
                            f"Cloudflare Turnstile widget detected with ID: {widget_id}"
                        )
                        logging.info("Waiting for Turnstile to complete...")

                        # Wait for Turnstile to complete (up to 60 seconds)
                        max_wait = 60
                        wait_time = 0

                        while wait_time < max_wait:
                            time.sleep(3)
                            wait_time += 3

                            # Check if Turnstile response is filled
                            try:
                                response_value = turnstile_widget.get_attribute("value")
                                if response_value and len(response_value) > 10:
                                    logging.info("Turnstile verification completed!")
                                    turnstile_found = True
                                    break
                                else:
                                    logging.info(
                                        f"Still waiting for Turnstile... ({wait_time}/{max_wait}s)"
                                    )
                            except:
                                pass

                        if turnstile_found:
                            break

                    except NoSuchElementException:
                        continue

                if not turnstile_found:
                    logging.info("No Cloudflare Turnstile widget found")

            # Enhanced button enable strategies
            logging.info("Login button is disabled, trying to enable it...")

            # Strategy 1: Wait for natural validation
            time.sleep(3)

            # Strategy 2: Trigger input events
            try:
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                    username_field,
                )
                time.sleep(1)
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                    password_field,
                )
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Strategy 2 failed: {e}")

            # Strategy 3: Trigger change events
            try:
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    username_field,
                )
                time.sleep(1)
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    password_field,
                )
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Strategy 3 failed: {e}")

            # Strategy 4: Trigger blur events
            try:
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));",
                    username_field,
                )
                time.sleep(1)
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));",
                    password_field,
                )
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Strategy 4 failed: {e}")

            # Strategy 5: Click outside to trigger validation
            try:
                self.driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Strategy 5 failed: {e}")

            # Strategy 6: Tab through fields
            try:
                username_field.send_keys(Keys.TAB)
                time.sleep(1)
                password_field.send_keys(Keys.TAB)
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Strategy 6 failed: {e}")

            # Strategy 7: Wait longer for validation
            try:
                time.sleep(5)
            except Exception as e:
                logging.warning(f"Strategy 7 failed: {e}")

            # Find and click login button with multiple strategies
            login_clicked = False
            login_button_selectors = [
                (By.ID, "signin_btn"),
                (By.CSS_SELECTOR, "button[data-cy='sign-in-btn']"),
                (By.CSS_SELECTOR, "button.btn__3Y3g"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button.btn"),
                (By.CSS_SELECTOR, "button[class*='btn']"),
                (By.CSS_SELECTOR, "button[class*='submit']"),
                (By.CSS_SELECTOR, "button[class*='login']"),
                (By.CSS_SELECTOR, "button[class*='signin']"),
            ]

            for by, selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)

                    # Check if button is disabled
                    if login_button.get_attribute("disabled"):
                        logging.warning(
                            "Login button is still disabled, trying to enable it..."
                        )

                        # Try to remove disabled attribute
                        try:
                            self.driver.execute_script(
                                "arguments[0].removeAttribute('disabled');",
                                login_button,
                            )
                            logging.info("Removed disabled attribute")
                        except Exception as e:
                            logging.warning(f"Could not remove disabled attribute: {e}")

                    # Try to click the button
                    try:
                        login_button.click()
                        logging.info("Login button clicked")
                        login_clicked = True
                        break
                    except Exception as e:
                        logging.warning(f"Could not click button: {e}")
                        # Try JavaScript click
                        try:
                            self.driver.execute_script(
                                "arguments[0].click();", login_button
                            )
                            logging.info("Login button clicked via JavaScript")
                            login_clicked = True
                            break
                        except Exception as e2:
                            logging.warning(f"JavaScript click failed: {e2}")
                            continue

                except NoSuchElementException:
                    continue

            if not login_clicked:
                logging.error("Login button not found, trying alternative methods...")

                # Try pressing Enter key
                try:
                    password_field.send_keys(Keys.RETURN)
                    logging.info("Login attempted with Enter key")
                    login_clicked = True
                except:
                    pass

                # Try form submission
                if not login_clicked:
                    try:
                        form = self.driver.find_element(By.TAG_NAME, "form")
                        self.driver.execute_script("arguments[0].submit();", form)
                        logging.info("Form submitted via JavaScript")
                        login_clicked = True
                    except Exception as e:
                        logging.warning(f"Form submission failed: {e}")

            if not login_clicked:
                logging.error("Could not find or click login button")
                return False, "Login button not found"

            # Wait for login to complete
            time.sleep(8)

            # Check if login was successful
            try:
                # Check if we're still on login page
                current_url = self.driver.current_url
                if "accounts/login" in current_url or "signin" in current_url:
                    logging.error("Still on login page, checking for errors...")

                    # Check for error messages
                    error_selectors = [
                        "//div[contains(@class, 'error')]",
                        "//div[contains(@class, 'alert')]",
                        "//span[contains(@class, 'error')]",
                        "//p[contains(@class, 'error')]",
                        "//div[contains(text(), 'Invalid')]",
                        "//div[contains(text(), 'Incorrect')]",
                        "//div[contains(text(), 'Failed')]",
                        "//p[contains(@class, 'error-message__3Q-C')]",  # From your HTML
                    ]

                    for selector in error_selectors:
                        try:
                            error_element = self.driver.find_element(By.XPATH, selector)
                            error_text = error_element.text.lower()
                            if (
                                "invalid" in error_text
                                or "incorrect" in error_text
                                or "failed" in error_text
                                or "wrong" in error_text
                            ):
                                logging.error(f"Login failed: {error_text}")
                                return False, f"Login failed: {error_text}"
                        except NoSuchElementException:
                            continue

                    # Check for Turnstile verification requirement
                    try:
                        turnstile_response = self.driver.find_element(
                            By.NAME, "cf-turnstile-response"
                        )
                        response_value = turnstile_response.get_attribute("value")
                        if not response_value or len(response_value) < 10:
                            logging.error(
                                "Turnstile verification required but not completed"
                            )

                            # Try to find and click manual verification checkbox
                            try:
                                manual_checkbox_selectors = [
                                    "//input[@type='checkbox']",
                                    "//input[contains(@class, 'checkbox')]",
                                    "//div[contains(@class, 'checkbox')]//input",
                                    "//label[contains(text(), 'Verify')]//input",
                                    "//div[contains(text(), 'Verify you are human')]//input",
                                    "//input[contains(@aria-label, 'Verify')]",
                                ]

                                checkbox_found = False
                                for selector in manual_checkbox_selectors:
                                    try:
                                        checkbox = self.driver.find_element(
                                            By.XPATH, selector
                                        )
                                        if not checkbox.is_selected():
                                            checkbox.click()
                                            logging.info(
                                                "Manual verification checkbox clicked"
                                            )
                                            time.sleep(3)  # Wait for verification
                                            checkbox_found = True
                                            break
                                    except NoSuchElementException:
                                        continue

                                if not checkbox_found:
                                    logging.warning(
                                        "Manual verification checkbox not found"
                                    )

                            except Exception as e:
                                logging.warning(
                                    f"Error handling manual verification: {e}"
                                )

                            return (
                                False,
                                "Turnstile verification required but not completed",
                            )
                    except NoSuchElementException:
                        pass

                    logging.error("Login failed - still on login page")
                    return False, "Login failed"

                else:
                    logging.info("Login successful - redirected from login page")
                    self.is_logged_in = True
                    return True, "Login successful"

            except Exception as e:
                logging.error(f"Error checking login status: {e}")
                return False, f"Error checking login status: {e}"

        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False, f"Login error: {e}"

    def submit_leetcode_solution(self, problem_slug, code, max_retries=3):
        """Submit C++ solution to LeetCode with enhanced test case validation"""
        if not self.driver:
            return False, "Driver not available - browser automation disabled"

        # Login to LeetCode if not already logged in
        if not self.is_logged_in:
            login_success, login_message = self.login_to_leetcode()
            if not login_success:
                return False, f"Login failed: {login_message}"

        try:
            # Navigate to the problem
            url = f"https://leetcode.com/problems/{problem_slug}/"
            print(f"Navigating to: {url}")
            self.driver.get(url)

            # Wait for page to load with multiple strategies
            editor_found = False
            wait_time = 30  # Increased timeout

            try:
                # Strategy 1: Wait for monaco editor
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "monaco-editor"))
                )
                editor_found = True
                print("Page loaded successfully (monaco editor)")
            except TimeoutException:
                print("Monaco editor not found, trying alternative selectors...")

                # Strategy 2: Try alternative editor selectors
                alternative_selectors = [
                    "[data-cy='code-editor']",
                    ".CodeMirror",
                    ".ace_editor",
                    "[class*='editor']",
                    "[class*='code']",
                    "textarea",
                ]

                for selector in alternative_selectors:
                    try:
                        editor = self.driver.find_element(By.CSS_SELECTOR, selector)
                        editor_found = True
                        print(f"Found editor with selector: {selector}")
                        break
                    except:
                        continue

                if not editor_found:
                    print("Could not find any code editor on page")
                    return False, "Could not find code editor on page"

            # Try to switch to C++ language
            try:
                # Look for language selector
                language_selectors = [
                    "//button[contains(@class, 'language-selector')]",
                    "//div[contains(@class, 'language-selector')]",
                    "//select[contains(@class, 'language')]",
                    "//button[contains(text(), 'C++')]",
                ]

                for selector in language_selectors:
                    try:
                        language_dropdown = self.driver.find_element(By.XPATH, selector)
                        language_dropdown.click()
                        time.sleep(2)

                        # Look for C++ option
                        cpp_selectors = [
                            "//div[contains(text(), 'C++')]",
                            "//option[contains(text(), 'C++')]",
                            "//li[contains(text(), 'C++')]",
                        ]

                        for cpp_selector in cpp_selectors:
                            try:
                                cpp_option = self.driver.find_element(
                                    By.XPATH, cpp_selector
                                )
                                cpp_option.click()
                                time.sleep(2)
                                print("Switched to C++ language")
                                break
                            except:
                                continue
                        break
                    except:
                        continue

            except Exception as e:
                print(f"⚠️ Could not switch to C++, using default language: {e}")

            # Find the code editor and paste the solution
            editor = None
            editor_selectors = [
                (By.CLASS_NAME, "monaco-editor"),
                (By.CSS_SELECTOR, "[data-cy='code-editor']"),
                (By.CSS_SELECTOR, ".CodeMirror"),
                (By.CSS_SELECTOR, ".ace_editor"),
                (By.CSS_SELECTOR, "[class*='editor']"),
                (By.TAG_NAME, "textarea"),
            ]

            for by, selector in editor_selectors:
                try:
                    editor = self.driver.find_element(by, selector)
                    break
                except:
                    continue

            if not editor:
                return False, "Could not find code editor"

            # Clear and paste code
            try:
                # Click on editor to focus
                self.driver.execute_script("arguments[0].click();", editor)
                time.sleep(1)

                # Clear existing code
                self.driver.find_element(By.TAG_NAME, "body").send_keys("ctrl+a")
                time.sleep(1)
                self.driver.find_element(By.TAG_NAME, "body").send_keys("delete")
                time.sleep(1)

                # Paste new code
                self.driver.find_element(By.TAG_NAME, "body").send_keys(code)
                print("Code pasted successfully")

            except Exception as e:
                print(f"Error pasting code: {e}")
                # Try alternative paste method
                try:
                    self.driver.execute_script(
                        f"arguments[0].value = `{code}`;", editor
                    )
                    print("Code pasted using JavaScript")
                except:
                    return False, "Could not paste code into editor"

            # Find and click submit button
            submit_clicked = False
            submit_selectors = [
                "button[data-e2e-locator='console-submit-button']",  # Primary selector based on HTML
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Run')]",
                "[data-cy='submit-code-btn']",
                "[data-cy='run-code-btn']",
                "//button[contains(@class, 'submit')]",
                "//button[contains(@class, 'run')]",
                "button[data-cid]",  # Alternative selector
            ]

            # Add timeout for submit button search
            submit_timeout = 30  # 30 seconds timeout
            submit_start_time = time.time()

            while (
                not submit_clicked
                and (time.time() - submit_start_time) < submit_timeout
            ):
                for selector in submit_selectors:
                    try:
                        submit_btn = self.driver.find_element(
                            By.XPATH if selector.startswith("//") else By.CSS_SELECTOR,
                            selector,
                        )

                        # Check if button is visible and clickable
                        if submit_btn.is_displayed() and submit_btn.is_enabled():
                            submit_btn.click()
                            logging.info("Submission sent...")
                            submit_clicked = True
                            break
                        else:
                            logging.warning(
                                f"Submit button found but not clickable: {selector}"
                            )
                            continue
                    except Exception as e:
                        logging.debug(
                            f"Submit button not found with selector {selector}: {e}"
                        )
                        continue

                if not submit_clicked:
                    logging.info("Submit button not found, waiting 2 seconds...")
                    time.sleep(2)

            if not submit_clicked:
                logging.error("Could not find submit button within timeout")
                return False, "Could not find submit button"

            # Wait for submission result with timeout
            logging.info("Waiting for submission result...")
            result_timeout = 30  # 30 seconds timeout for result
            result_start_time = time.time()

            while (time.time() - result_start_time) < result_timeout:
                try:
                    # Check for various result indicators
                    result_selectors = [
                        "div[data-cy='submission-result']",
                        "div.result__2cm",
                        "div[class*='result']",
                        "div[class*='submission']",
                        "div[class*='status']",
                        "div[class*='error']",
                    ]

                    result_text = ""
                    for selector in result_selectors:
                        try:
                            result_element = self.driver.find_element(
                                By.CSS_SELECTOR, selector
                            )
                            result_text = result_element.text
                            if result_text:
                                break
                        except:
                            continue

                    # Also check for specific success/failure indicators
                    page_text = self.driver.page_source.lower()

                    # Success indicators
                    if "accepted" in result_text.lower() or "accepted" in page_text:
                        return True, "Accepted - All test cases passed!"

                    # Failure indicators with specific messages
                    if (
                        "wrong answer" in result_text.lower()
                        or "wrong answer" in page_text
                    ):
                        return False, "Wrong Answer - Test case failed"

                    if (
                        "runtime error" in result_text.lower()
                        or "runtime error" in page_text
                    ):
                        return False, "Runtime Error - Code execution failed"

                    if (
                        "time limit exceeded" in result_text.lower()
                        or "time limit exceeded" in page_text
                    ):
                        return False, "Time Limit Exceeded - Solution too slow"

                    if (
                        "memory limit exceeded" in result_text.lower()
                        or "memory limit exceeded" in page_text
                    ):
                        return False, "Memory Limit Exceeded - Too much memory used"

                    if (
                        "compilation error" in result_text.lower()
                        or "compilation error" in page_text
                    ):
                        return False, "Compilation Error - Code doesn't compile"

                    if (
                        "presentation error" in result_text.lower()
                        or "presentation error" in page_text
                    ):
                        return False, "Presentation Error - Output format issue"

                    # If we can't determine the result, check for any error messages
                    if result_text:
                        return False, f"Submission failed: {result_text}"

                    # Wait a bit before checking again
                    time.sleep(2)

                except Exception as e:
                    logging.debug(f"Error checking submission result: {e}")
                    time.sleep(2)

            # Timeout reached
            logging.error("Submission result timeout - could not determine result")
            return False, "Could not determine submission result within timeout"

        except WebDriverException as e:
            return False, f"WebDriver error: {str(e)}"
        except Exception as e:
            return False, f"Error submitting C++ solution to LeetCode: {e}"

    def submit_gfg_solution(self, problem_url, code, max_retries=3):
        """Submit C++ solution to GFG"""
        if not self.driver:
            return False, "Driver not available"

        try:
            # Navigate to the problem
            self.driver.get(problem_url)

            # Wait for page to load with timeout
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ace_editor"))
                )
            except TimeoutException:
                return False, "Could not load GFG page within timeout"

            # Switch to C++ language if available
            try:
                language_dropdown = self.driver.find_element(
                    By.XPATH, "//select[@id='language']"
                )
                from selenium.webdriver.support.ui import Select

                select = Select(language_dropdown)
                select.select_by_visible_text("C++")
                time.sleep(2)
            except:
                logging.warning("Could not switch to C++, using default language")

            # Find the code editor and paste the solution
            editor = self.driver.find_element(By.CLASS_NAME, "ace_editor")
            self.driver.execute_script("arguments[0].click();", editor)

            # Clear existing code and paste new code
            self.driver.find_element(By.TAG_NAME, "body").send_keys("ctrl+a")
            self.driver.find_element(By.TAG_NAME, "body").send_keys("delete")
            self.driver.find_element(By.TAG_NAME, "body").send_keys(code)

            # Click submit button with timeout
            submit_timeout = 30
            submit_start_time = time.time()
            submit_clicked = False

            while (
                not submit_clicked
                and (time.time() - submit_start_time) < submit_timeout
            ):
                try:
                    submit_btn = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Submit')]"
                    )
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        submit_clicked = True
                        break
                    else:
                        logging.warning("Submit button found but not clickable")
                        time.sleep(2)
                except Exception as e:
                    logging.debug(f"Submit button not found: {e}")
                    time.sleep(2)

            if not submit_clicked:
                return False, "Could not find or click submit button within timeout"

            # Wait for submission result with timeout
            result_timeout = 30
            result_start_time = time.time()

            while (time.time() - result_start_time) < result_timeout:
                try:
                    result_element = self.driver.find_element(
                        By.CLASS_NAME, "alert-success"
                    )
                    return True, "C++ solution accepted"
                except NoSuchElementException:
                    try:
                        result_element = self.driver.find_element(
                            By.CLASS_NAME, "alert-danger"
                        )
                        return False, f"C++ solution failed: {result_element.text}"
                    except NoSuchElementException:
                        # Wait a bit before checking again
                        time.sleep(2)
                        continue

            return False, "Could not determine submission result within timeout"

        except Exception as e:
            return False, f"Error submitting C++ solution to GFG: {e}"

    def send_solution_email(
        self, platform, problem_title, problem_url, solution, error_message
    ):
        """Send solution to email when submission fails or login issues occur"""
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = EMAIL_ADDRESS
            msg["Subject"] = f"POTD Solution - {platform} - {problem_title}"

            body = f"""
            Daily POTD Solution Generated

            Platform: {platform}
            Problem: {problem_title}
            URL: {problem_url}
            Error: {error_message}

            The automated system generated a solution but could not submit it due to login/UI issues.
            Please manually submit the solution below.

            Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
            """

            # Add solution code if available
            if solution and solution.strip():
                body += f"\n\nGenerated Solution:\n```cpp\n{solution}\n```"
            else:
                body += "\n\nNo solution was generated."

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

            try:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                text = msg.as_string()
                server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, text)
                server.quit()
                logging.info(f"Solution email sent for {platform} - {problem_title}")
            except smtplib.SMTPAuthenticationError:
                logging.error(
                    "Email authentication failed. Please check your EMAIL_ADDRESS and EMAIL_PASSWORD."
                )
                logging.error(
                    f"Solution: {platform} - {problem_title} - {error_message}"
                )
            except Exception as e:
                logging.error(f"Email sending failed: {e}")
                logging.error(
                    f"Solution: {platform} - {problem_title} - {error_message}"
                )

        except Exception as e:
            logging.error(f"Error setting up solution email: {e}")
            logging.error(f"Solution: {platform} - {problem_title} - {error_message}")

    def send_email_notification(self, platform, problem_title, error_message):
        """Send email notification when solution fails after max retries"""
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = EMAIL_ADDRESS
            msg["Subject"] = f"POTD Solution Failed - {platform}"

            body = f"""
            Daily POTD Solution Failed

            Platform: {platform}
            Problem: {problem_title}
            Error: {error_message}

            The automated system was unable to generate a correct solution after 3 attempts.
            Please check the problem manually.

            Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
            """

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

            try:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                text = msg.as_string()
                server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, text)
                server.quit()
                print(f"Email notification sent for {platform} - {problem_title}")
            except smtplib.SMTPAuthenticationError:
                print(
                    f"Email authentication failed. Please check your EMAIL_ADDRESS and EMAIL_PASSWORD."
                )
                print(f"Failure: {platform} - {problem_title} - {error_message}")
            except Exception as e:
                print(f"Email sending failed: {e}")
                print(f"Failure: {platform} - {problem_title} - {error_message}")

        except Exception as e:
            print(f"Error setting up email notification: {e}")
            print(f"Failure: {platform} - {problem_title} - {error_message}")

    def close_driver(self):
        """Close the web driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
