import time
import threading
import logging
from problem_fetcher import get_leetcode_potd
from enhanced_solution_manager import generate_and_test_solution
from submission_manager import SubmissionManager
from solution_manager import load_local_solution, save_solution
from config import check_api_keys


class TimeoutError(Exception):
    pass


def timeout_handler(func, timeout_seconds, *args, **kwargs):
    result, exception = [None], [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    if thread.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    if exception[0]:
        raise exception[0]
    return result[0]


class AutomatedPOTDSystem:
    def __init__(self):
        self.submission_manager = SubmissionManager()
        self.max_retries = 2
        self.global_timeout = 900
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def run_with_timeout(self, func, *args, **kwargs):
        try:
            return timeout_handler(func, self.global_timeout, *args, **kwargs)
        except TimeoutError as e:
            logging.error(str(e))
            return False
        except Exception as e:
            logging.error(f"An unhandled exception occurred: {e}", exc_info=True)
            return False

    def process_platform(self, platform_name, fetch_func, submit_func):
        logging.info("=" * 50 + f"\nProcessing {platform_name} POTD\n" + "=" * 50)

        # If the driver failed to initialize, we can't proceed with browser-based tasks.
        if not self.submission_manager.driver:
            logging.error(
                f"Cannot process {platform_name} because the browser driver is not available."
            )
            return False

        try:
            title, slug_or_url, url = fetch_func()
            if "Error" in title:
                logging.error(f"Failed to fetch {platform_name} POTD: {title}")
                return False

            logging.info(f"{platform_name} POTD: {title}\nURL: {url}")
            slug = (
                slug_or_url
                if platform_name == "LeetCode"
                else title.lower().replace(" ", "-")
            )

            solution, found = load_local_solution(platform_name.lower(), slug)
            if not found:
                logging.info("No local solution found. Generating new one...")
                solution, _, success = generate_and_test_solution(
                    title, url, self.max_retries
                )
                if not success:
                    error_msg = f"Failed to generate a compilable solution after {self.max_retries} attempts."
                    self.submission_manager.send_failure_notification(
                        platform_name, title, error_msg
                    )
                    return False
                save_solution(platform_name.lower(), slug, solution)

            logging.info(f"Submitting solution to {platform_name}...")
            success, message = submit_func(slug_or_url, solution)

            if success:
                logging.info(
                    f"{platform_name} solution submitted successfully! Result: {message}"
                )
                return True
            else:
                logging.error(f"{platform_name} submission failed: {message}")
                is_ui_failure = (
                    "timeout" in message.lower()
                    or "login" in message.lower()
                    or "captcha" in message.lower()
                    or "driver" in message.lower()
                )

                if is_ui_failure:
                    logging.warning(
                        "Critical UI/Login failure detected. Sending solution to email."
                    )
                    self.submission_manager.send_solution_email(
                        platform_name,
                        title,
                        url,
                        solution,
                        f"Submission UI Failure: {message}",
                    )
                else:
                    logging.warning(
                        "Submission failed, likely due to solution correctness (e.g., Wrong Answer)."
                    )
                    self.submission_manager.send_failure_notification(
                        platform_name, title, f"Submission Failed: {message}"
                    )
                return False

        except Exception as e:
            logging.error(
                f"An unexpected error occurred while processing {platform_name}: {e}",
                exc_info=True,
            )
            self.submission_manager.send_failure_notification(
                platform_name, "Unknown", f"An unexpected error occurred: {e}"
            )
            return False

    def process_leetcode_potd(self):
        return self.run_with_timeout(
            self.process_platform,
            "LeetCode",
            get_leetcode_potd,
            self.submission_manager.submit_leetcode_solution,
        )

    def process_gfg_potd(self):
        # --- KEY FIX: Use the browser-based fetcher from the submission manager ---
        return self.run_with_timeout(
            self.process_platform,
            "GFG",
            self.submission_manager.get_gfg_potd_with_browser,
            self.submission_manager.submit_gfg_solution,
        )

    def run_daily(self):
        logging.info("Starting Automated Daily POTD System")
        if not check_api_keys():
            logging.error("API keys not configured. Exiting.")
            return

        leetcode_success = self.process_leetcode_potd()
        gfg_success = self.process_gfg_potd()

        logging.info(
            "=" * 60
            + "\nDaily POTD Summary\n"
            + f"  LeetCode: {'SUCCESS' if leetcode_success else 'FAILED'}\n"
            + f"  GFG:      {'SUCCESS' if gfg_success else 'FAILED'}\n"
            + "=" * 60
        )
        self.submission_manager.close_driver()
        logging.info("Automated POTD system run completed.")


def main():
    system = AutomatedPOTDSystem()
    system.run_daily()


if __name__ == "__main__":
    main()
