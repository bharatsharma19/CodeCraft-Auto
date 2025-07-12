import time
import threading
from problem_fetcher import get_leetcode_potd, get_gfg_potd
from enhanced_solution_manager import (
    generate_and_test_solution,
    validate_solution_structure,
)
from submission_manager import SubmissionManager
from solution_manager import load_local_solution, save_solution
from config import check_api_keys, check_email_config
import logging


class TimeoutError(Exception):
    pass


def timeout_handler(func, *args, **kwargs):
    """Execute function with timeout using threading"""
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=600)  # 10 minutes timeout

    if thread.is_alive():
        raise TimeoutError("Operation timed out after 10 minutes")

    if exception[0]:
        raise exception[0]

    return result[0]


class AutomatedPOTDSystem:
    def __init__(self):
        self.submission_manager = SubmissionManager()
        self.max_retries = 2  # Reduced from 3 to 2
        self.global_timeout = 600  # 10 minutes global timeout
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
        )

    def run_with_timeout(self, func, *args, **kwargs):
        """Run a function with a timeout using threading"""
        try:
            return timeout_handler(func, *args, **kwargs)
        except TimeoutError:
            logging.error("Operation timed out after 10 minutes")
            return False
        except Exception as e:
            logging.error(f"Error in operation: {e}")
            return False

    def process_leetcode_potd(self):
        """Process LeetCode POTD with automated submission and testing"""
        return self.run_with_timeout(self._process_leetcode_potd_internal)

    def _process_leetcode_potd_internal(self):
        """Internal method for processing LeetCode POTD"""
        logging.info("=" * 50)
        logging.info("Processing LeetCode POTD")
        logging.info("=" * 50)

        try:
            # Fetch LeetCode POTD
            lc_title, lc_slug, lc_url = get_leetcode_potd()
            logging.info(f"LeetCode POTD: {lc_title}")
            logging.info(f"URL: {lc_url}")

            # Check if we already have a solution
            lc_solution, found = load_local_solution("leetcode", lc_slug)
            if found:
                logging.info("Found existing solution, testing it...")
                # Test the existing solution
                success, message = self.test_solution(lc_solution, lc_title, lc_url)
                if not success:
                    logging.warning(f"Existing solution failed tests: {message}")
                    lc_solution = None  # Will regenerate
                else:
                    logging.info("Existing solution passed tests")
            else:
                logging.info("No existing solution found, generating new one...")
                lc_solution = None

            # Generate new solution if needed
            if not lc_solution:
                logging.info("Generating and testing solution...")
                lc_solution, attempt, success = generate_and_test_solution(
                    lc_title, lc_url, self.max_retries
                )

                if not success:
                    logging.error(
                        f"Failed to generate working solution after {self.max_retries} attempts"
                    )
                    # Send solution to email when generation fails
                    self.send_solution_to_email(
                        "LeetCode", lc_title, lc_url, lc_solution, "Generation failed"
                    )
                    return False

                # Save the working solution
                save_solution("leetcode", lc_slug, lc_solution)
                logging.info(f"Solution generated and saved (attempt {attempt})")

            # Validate solution structure
            if not validate_solution_structure(lc_solution):
                logging.error("Generated solution has invalid structure")
                self.send_solution_to_email(
                    "LeetCode", lc_title, lc_url, lc_solution, "Invalid structure"
                )
                return False

            # Submit solution
            logging.info("Submitting solution to LeetCode...")
            success, message = self.submission_manager.submit_leetcode_solution(
                lc_slug, lc_solution
            )

            if success:
                logging.info("LeetCode solution submitted successfully!")
                return True
            else:
                logging.error(f"LeetCode submission failed: {message}")

                # Check if it's a login failure or other critical issue
                is_login_failure = (
                    "Login failed" in message
                    or "Could not find submit button" in message
                    or "Driver not available" in message
                    or "Could not find code editor" in message
                    or "timeout" in message.lower()
                )

                if is_login_failure:
                    logging.warning(
                        "Login/UI failure detected - sending solution to email"
                    )
                    self.send_solution_to_email(
                        "LeetCode",
                        lc_title,
                        lc_url,
                        lc_solution,
                        f"Login/UI failure: {message}",
                    )
                    return False
                else:
                    # Check if it's a solution correctness failure
                    is_solution_failure = (
                        "Wrong Answer" in message
                        or "Runtime Error" in message
                        or "Time Limit Exceeded" in message
                        or "Compilation Error" in message
                        or "Memory Limit Exceeded" in message
                    )

                    if is_solution_failure:
                        logging.warning(
                            "Solution correctness failure - will generate new solution"
                        )
                        # Try to regenerate and resubmit
                        for retry in range(1, self.max_retries + 1):
                            logging.info(
                                f"Retrying with new solution (attempt {retry}/{self.max_retries})..."
                            )

                            # Generate new solution
                            new_solution, attempt, success = generate_and_test_solution(
                                lc_title, lc_url, self.max_retries
                            )

                            if not success:
                                logging.error(
                                    f"Failed to generate working solution on retry {retry}"
                                )
                                continue

                            # Save new solution
                            save_solution("leetcode", lc_slug, new_solution)

                            # Submit new solution
                            success, message = (
                                self.submission_manager.submit_leetcode_solution(
                                    lc_slug, new_solution
                                )
                            )

                            if success:
                                logging.info(
                                    "LeetCode solution submitted successfully on retry!"
                                )
                                return True
                            else:
                                logging.error(f"Retry {retry} failed: {message}")

                        # All retries failed
                        self.send_solution_to_email(
                            "LeetCode",
                            lc_title,
                            lc_url,
                            lc_solution,
                            f"Failed after {self.max_retries} submission attempts",
                        )
                        return False
                    else:
                        logging.warning("Unknown failure - sending solution to email")
                        self.send_solution_to_email(
                            "LeetCode",
                            lc_title,
                            lc_url,
                            lc_solution,
                            f"Unknown failure: {message}",
                        )
                        return False

        except Exception as e:
            logging.error(f"Error processing LeetCode POTD: {e}")
            self.send_solution_to_email("LeetCode", "Unknown", "Unknown", "", str(e))
            return False

    def process_gfg_potd(self):
        """Process GFG POTD with automated submission and testing"""
        return self.run_with_timeout(self._process_gfg_potd_internal)

    def _process_gfg_potd_internal(self):
        """Internal method for processing GFG POTD"""
        logging.info("=" * 50)
        logging.info("Processing GFG POTD")
        logging.info("=" * 50)

        try:
            # Fetch GFG POTD
            gfg_title, gfg_url = get_gfg_potd()
            gfg_slug = gfg_title.lower().replace(" ", "_").replace("-", "_")
            logging.info(f"GFG POTD: {gfg_title}")
            logging.info(f"URL: {gfg_url}")

            # Check if we already have a solution
            gfg_solution, found = load_local_solution("gfg", gfg_slug)
            if found:
                logging.info("Found existing solution, testing it...")
                # Test the existing solution
                success, message = self.test_solution(gfg_solution, gfg_title, gfg_url)
                if not success:
                    logging.warning(f"Existing solution failed tests: {message}")
                    gfg_solution = None  # Will regenerate
                else:
                    logging.info("Existing solution passed tests")
            else:
                logging.info("No existing solution found, generating new one...")
                gfg_solution = None

            # Generate new solution if needed
            if not gfg_solution:
                logging.info("Generating and testing solution...")
                gfg_solution, attempt, success = generate_and_test_solution(
                    gfg_title, gfg_url, self.max_retries
                )

                if not success:
                    logging.error(
                        f"Failed to generate working solution after {self.max_retries} attempts"
                    )
                    # Send solution to email when generation fails
                    self.send_solution_to_email(
                        "GFG", gfg_title, gfg_url, gfg_solution, "Generation failed"
                    )
                    return False

                # Save the working solution
                save_solution("gfg", gfg_slug, gfg_solution)
                logging.info(f"Solution generated and saved (attempt {attempt})")

            # Validate solution structure
            if not validate_solution_structure(gfg_solution):
                logging.error("Generated solution has invalid structure")
                self.send_solution_to_email(
                    "GFG", gfg_title, gfg_url, gfg_solution, "Invalid structure"
                )
                return False

            # Submit solution
            logging.info("Submitting solution to GFG...")
            success, message = self.submission_manager.submit_gfg_solution(
                gfg_url, gfg_solution
            )

            if success:
                logging.info("GFG solution submitted successfully!")
                return True
            else:
                logging.error(f"GFG submission failed: {message}")

                # Check if it's a login failure or other critical issue
                is_login_failure = (
                    "Login failed" in message
                    or "Could not find submit button" in message
                    or "Driver not available" in message
                    or "Could not find code editor" in message
                    or "timeout" in message.lower()
                )

                if is_login_failure:
                    logging.warning(
                        "Login/UI failure detected - sending solution to email"
                    )
                    self.send_solution_to_email(
                        "GFG",
                        gfg_title,
                        gfg_url,
                        gfg_solution,
                        f"Login/UI failure: {message}",
                    )
                    return False
                else:
                    # Check if it's a solution correctness failure
                    is_solution_failure = (
                        "Wrong Answer" in message
                        or "Runtime Error" in message
                        or "Time Limit Exceeded" in message
                        or "Compilation Error" in message
                        or "Memory Limit Exceeded" in message
                    )

                    if is_solution_failure:
                        logging.warning(
                            "Solution correctness failure - will generate new solution"
                        )
                        # Try to regenerate and resubmit
                        for retry in range(1, self.max_retries + 1):
                            logging.info(
                                f"Retrying with new solution (attempt {retry}/{self.max_retries})..."
                            )

                            # Generate new solution
                            new_solution, attempt, success = generate_and_test_solution(
                                gfg_title, gfg_url, self.max_retries
                            )

                            if not success:
                                logging.error(
                                    f"Failed to generate working solution on retry {retry}"
                                )
                                continue

                            # Save new solution
                            save_solution("gfg", gfg_slug, new_solution)

                            # Submit new solution
                            success, message = (
                                self.submission_manager.submit_gfg_solution(
                                    gfg_url, new_solution
                                )
                            )

                            if success:
                                logging.info(
                                    "GFG solution submitted successfully on retry!"
                                )
                                return True
                            else:
                                logging.error(f"Retry {retry} failed: {message}")

                        # All retries failed
                        self.send_solution_to_email(
                            "GFG",
                            gfg_title,
                            gfg_url,
                            gfg_solution,
                            f"Failed after {self.max_retries} submission attempts",
                        )
                        return False
                    else:
                        logging.warning("Unknown failure - sending solution to email")
                        self.send_solution_to_email(
                            "GFG",
                            gfg_title,
                            gfg_url,
                            gfg_solution,
                            f"Unknown failure: {message}",
                        )
                        return False

        except Exception as e:
            logging.error(f"Error processing GFG POTD: {e}")
            self.send_solution_to_email("GFG", "Unknown", "Unknown", "", str(e))
            return False

    def test_solution(self, solution, problem_title, problem_url):
        """Test a solution against test cases"""
        from enhanced_solution_manager import test_solution_with_cases

        return test_solution_with_cases(solution, problem_title, problem_url)

    def send_solution_to_email(
        self, platform, problem_title, problem_url, solution, error_message
    ):
        """Send solution to email when submission fails or login issues occur"""
        if check_email_config():
            self.submission_manager.send_solution_email(
                platform, problem_title, problem_url, solution, error_message
            )
        else:
            logging.warning("Email notification skipped - email not configured")
            logging.error(f"Failure: {platform} - {problem_title} - {error_message}")

    def send_failure_notification(self, platform, problem_title, error_message):
        """Send email notification for failures"""
        if check_email_config():
            self.submission_manager.send_email_notification(
                platform, problem_title, error_message
            )
        else:
            logging.warning("Email notification skipped - email not configured")
            logging.error(f"Failure: {platform} - {problem_title} - {error_message}")

    def run_daily(self):
        """Run the complete daily POTD automation with testing"""
        logging.info("Starting Enhanced Automated Daily POTD System")
        logging.info("=" * 60)

        # Check configurations
        if not check_api_keys():
            logging.error("API keys not configured. Please set environment variables.")
            return

        # Process both platforms
        leetcode_success = self.process_leetcode_potd()
        gfg_success = self.process_gfg_potd()

        # Summary
        logging.info("=" * 60)
        logging.info("Daily POTD Summary")
        logging.info("=" * 60)
        logging.info(f"LeetCode: {'Success' if leetcode_success else 'Failed'}")
        logging.info(f"GFG: {'Success' if gfg_success else 'Failed'}")

        # Cleanup
        self.submission_manager.close_driver()
        logging.info("Enhanced automated POTD system completed")


def main():
    """Main function to run the automated system"""
    system = AutomatedPOTDSystem()
    system.run_daily()


if __name__ == "__main__":
    main()
