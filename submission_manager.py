import time
import smtplib
import logging
import html
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin

from config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
    LEETCODE_USERNAME,
    LEETCODE_PASSWORD,
    GFG_USERNAME,
    GFG_PASSWORD,
    CHROME_USER_DATA_DIR,
    check_leetcode_config,
    check_gfg_config,
    check_email_config,
)


class SubmissionManager:
    def __init__(self):
        self.driver = None
        self.leetcode_logged_in = False
        self.gfg_logged_in = False
        self.setup_driver()

    def setup_driver(self):
        try:
            logging.info("Setting up Chrome driver with persistent user profile...")
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            if not os.path.exists(CHROME_USER_DATA_DIR):
                os.makedirs(CHROME_USER_DATA_DIR)
            options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            logging.info(
                f"Chrome driver setup successful. Profile: {CHROME_USER_DATA_DIR}"
            )
        except Exception as e:
            logging.error(f"Fatal error setting up Chrome driver: {e}", exc_info=True)
            self.driver = None

    def login_to_leetcode(self):
        if not self.driver:
            return False, "Driver not available"
        if not check_leetcode_config():
            return False, "LeetCode credentials not configured"
        try:
            logging.info("Checking LeetCode login status...")
            self.driver.get("https://leetcode.com/")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "img[alt='avatar']")
                    )
                )
                logging.info("Already logged in to LeetCode.")
                self.leetcode_logged_in = True
                return True, "Login session restored."
            except TimeoutException:
                logging.warning(
                    "Not logged in to LeetCode. Please log in manually in the browser window."
                )
                self.driver.get("https://leetcode.com/accounts/login/")
                WebDriverWait(self.driver, 300).until(
                    lambda d: "leetcode.com/accounts/login/" not in d.current_url
                )
                logging.info("Login successful (likely manual). Session saved.")
                self.leetcode_logged_in = True
                return True, "Login successful."
        except Exception as e:
            return False, f"An unexpected error during LeetCode login: {e}"

    def login_to_gfg(self):
        if not self.driver:
            return False, "Driver not available"
        if not check_gfg_config():
            return False, "GFG credentials not configured"
        try:
            logging.info("Checking GFG login status...")
            self.driver.get("https://www.geeksforgeeks.org/")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[class*='header-main__profile']")
                    )
                )
                logging.info("Already logged in to GFG.")
                self.gfg_logged_in = True
                return True, "Login session restored."
            except TimeoutException:
                logging.warning("Not logged in to GFG. Attempting login...")
                self.driver.get("https://auth.geeksforgeeks.org/user/login")
                email_field = WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.ID, "luser"))
                )
                password_field = self.driver.find_element(By.ID, "password")
                email_field.send_keys(GFG_USERNAME)
                password_field.send_keys(GFG_PASSWORD)
                self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                ).click()
                WebDriverWait(self.driver, 20).until(
                    EC.url_contains("geeksforgeeks.org")
                )
                logging.info("GFG login successful.")
                self.gfg_logged_in = True
                return True, "Login successful."
        except Exception as e:
            return False, f"An unexpected error during GFG login: {e}"

    def get_gfg_potd_with_browser(self):
        if not self.driver:
            return "Error: Driver not available", "error", ""
        base_url = "https://www.geeksforgeeks.org/problem-of-the-day"
        try:
            self.driver.get(base_url)
            # This selector is based on the HTML you provided for the main POTD page.
            potd_link_selector = (
                "div[class*='problemOfTheDay_potd_banner'] a[href*='/problems/']"
            )
            potd_link_element = WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, potd_link_selector))
            )
            title = potd_link_element.text.strip()
            link = potd_link_element.get_attribute("href")
            return title, link, link
        except Exception as e:
            logging.error(f"Failed to fetch GFG POTD using browser: {e}", exc_info=True)
            return "Error fetching GFG POTD with browser", "error", base_url

    def submit_leetcode_solution(self, problem_slug, code):
        if not self.driver:
            return False, "Driver not available"
        if not self.leetcode_logged_in:
            success, message = self.login_to_leetcode()
            if not success:
                return False, f"Login failed: {message}"
        try:
            url = f"https://leetcode.com/problems/{problem_slug}/"
            self.driver.get(url)

            # --- THE FINAL PASTE FIX: Direct JS injection into the editor's textarea ---
            logging.info("Waiting for Monaco editor's textarea...")
            # The textarea is where the code actually lives.
            editor_textarea = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".monaco-editor textarea")
                )
            )

            logging.info("Pasting solution via direct JavaScript injection...")
            # This is the most reliable way to set the content of a complex editor.
            self.driver.execute_script(
                "arguments[0].value = arguments[1];", editor_textarea, code
            )

            submit_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button[data-e2e-locator='console-submit-button']",
                    )
                )
            )
            submit_button.click()

            success_selector = (
                "span[data-e2e-locator='submission-result'][class*='text-green']"
            )
            failure_selector = (
                "span[data-e2e-locator='submission-result'][class*='text-red']"
            )

            result_element = WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"{success_selector}, {failure_selector}")
                )
            )
            result_text = result_element.text
            return "Accepted" in result_text, result_text
        except Exception as e:
            return False, f"Error during LeetCode submission: {e}"

    def submit_gfg_solution(self, problem_url, code):
        if not self.driver:
            return False, "Driver not available"
        if not self.gfg_logged_in:
            success, message = self.login_to_gfg()
            if not success:
                return False, f"Login failed: {message}"
        try:
            self.driver.get(problem_url)
            editor = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ace_editor"))
            )
            self.driver.execute_script(
                "ace.edit(arguments[0]).setValue(arguments[1]);", editor, code
            )
            submit_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "form_submit"))
            )
            self.driver.execute_script("arguments[0].click();", submit_btn)

            success_selector = "div[class*='alert-success']"
            failure_selector = "div[class*='alert-danger']"

            result_element = WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"{success_selector}, {failure_selector}")
                )
            )
            result_text = result_element.text
            return "Correct Answer" in result_text, result_text
        except Exception as e:
            return False, f"Error submitting solution to GFG: {e}"

    # ... (Email and close_driver functions remain the same)
    def send_solution_email(
        self, platform, problem_title, problem_url, solution, error_message
    ):
        if not check_email_config():
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = EMAIL_ADDRESS
            msg["Subject"] = f"POTD Solution - {platform}: {problem_title}"
            escaped_solution = html.escape(solution)
            html_body = f"""
            <html><head><style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; }}
                .container {{ padding: 20px; border: 1px solid #e1e4e8; border-radius: 6px; max-width: 800px; margin: 20px auto; }}
                .header {{ font-size: 20px; font-weight: bold; color: #c9510c; border-bottom: 1px solid #e1e4e8; padding-bottom: 10px; margin-bottom: 15px; }}
                .info {{ margin-bottom: 15px; background-color: #f6f8fa; padding: 10px; border-radius: 6px; }}
                .info-label {{ font-weight: 600; }}
                pre.code-block {{ background-color: #2d2d2d; color: #f1f1f1; border: 1px solid #ddd; padding: 15px; border-radius: 6px; font-family: "Courier New", Courier, monospace; white-space: pre-wrap; word-wrap: break-word; }}
            </style></head><body><div class="container">
                <div class="header">Automated POTD System Alert</div>
                <p>A solution was generated but could not be submitted automatically.</p>
                <div class="info">
                    <span class="info-label">Platform:</span> {platform}<br>
                    <span class="info-label">Problem:</span> {problem_title}<br>
                    <span class="info-label">URL:</span> <a href="{problem_url}">{problem_url}</a><br>
                    <span class="info-label">Error:</span> {error_message}
                </div>
                <p class="info-label">Please manually submit the solution below:</p>
                <pre class="code-block"><code>{escaped_solution}</code></pre>
                <p style="font-size: 12px; color: #586069; text-align: center;">Time: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div></body></html>
            """
            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, [EMAIL_ADDRESS], msg.as_string())
                logging.info(f"Solution email sent for {platform} - {problem_title}")
        except Exception as e:
            logging.error(f"Failed to send solution email: {e}", exc_info=True)

    def send_failure_notification(self, platform, problem_title, error_message):
        if not check_email_config():
            return
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = EMAIL_ADDRESS
            msg["Subject"] = f"POTD FAILURE - {platform}: {problem_title}"
            body = f"Daily POTD Solution Generation FAILED\n\nPlatform: {platform}\nProblem: {problem_title}\nError: {error_message}\n\nThe automated system was unable to generate a working solution after all attempts.\nPlease check the problem manually.\n\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, [EMAIL_ADDRESS], msg.as_string())
                logging.info(
                    f"Failure notification sent for {platform} - {problem_title}"
                )
        except Exception as e:
            logging.error(f"Failed to send failure notification: {e}", exc_info=True)

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Chrome driver closed.")
            except Exception as e:
                logging.warning(f"Ignoring benign error during driver shutdown: {e}")
