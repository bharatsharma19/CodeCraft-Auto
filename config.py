# config.py
import os
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file
load_dotenv()

# --- AI Configuration ---
# Set USE_GEMINI to True to use Google Gemini, False for OpenAI
USE_GEMINI = os.getenv("USE_GEMINI", "True").lower() in ("true", "1", "t")

# API Keys - loaded from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")

# Model Names
OPENAI_MODEL_NAME = "gpt-4-turbo"
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"

# --- Email Configuration for Notifications ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD", "your-app-password"
)  # Use an App Password for Gmail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- LeetCode Login Credentials ---
LEETCODE_USERNAME = os.getenv("LEETCODE_USERNAME", "your-leetcode-username")
LEETCODE_PASSWORD = os.getenv("LEETCODE_PASSWORD", "your-leetcode-password")

# --- GFG Login Credentials ---
GFG_USERNAME = os.getenv("GFG_USERNAME", "your-gfg-email@example.com")
GFG_PASSWORD = os.getenv("GFG_PASSWORD", "your-gfg-password")

# --- Chrome Profile Path for Persistent Sessions ---
# This creates a 'chrome_profile' folder in your project directory to store login sessions.
CHROME_USER_DATA_DIR = os.path.join(os.getcwd(), "chrome_profile")

# --- Global AI Client Instances ---
openai_client = None
gemini_model = None


def initialize_ai_clients():
    """Initialize AI clients based on the configuration."""
    global openai_client, gemini_model

    if not USE_GEMINI and OPENAI_API_KEY != "your-openai-api-key":
        try:
            import openai

            openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logging.info("OpenAI client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")

    if USE_GEMINI and GEMINI_API_KEY != "your-gemini-api-key":
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            logging.info("Gemini client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini client: {e}")


# Initialize clients on module import
initialize_ai_clients()


def check_api_keys():
    """Check if the selected AI's API key is configured."""
    if USE_GEMINI:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key":
            logging.warning("USE_GEMINI is True, but GEMINI_API_KEY is not set.")
            return False
    else:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key":
            logging.warning("USE_GEMINI is False, but OPENAI_API_KEY is not set.")
            return False
    return True


def check_email_config():
    """Check if email credentials are configured."""
    if (
        not EMAIL_ADDRESS
        or EMAIL_ADDRESS == "your-email@gmail.com"
        or not EMAIL_PASSWORD
        or EMAIL_PASSWORD == "your-app-password"
    ):
        logging.warning(
            "Email configuration not set. Email notifications will be disabled."
        )
        return False
    return True


def check_leetcode_config():
    """Check if LeetCode credentials are configured."""
    if (
        not LEETCODE_USERNAME
        or LEETCODE_USERNAME == "your-leetcode-username"
        or not LEETCODE_PASSWORD
        or LEETCODE_PASSWORD == "your-leetcode-password"
    ):
        logging.warning(
            "LeetCode credentials not set. LeetCode submissions will be disabled."
        )
        return False
    return True


def check_gfg_config():
    """Check if GFG credentials are configured."""
    if (
        not GFG_USERNAME
        or GFG_USERNAME == "your-gfg-email@example.com"
        or not GFG_PASSWORD
        or GFG_PASSWORD == "your-gfg-password"
    ):
        logging.warning("GFG credentials not set. GFG submissions may fail.")
        return False
    return True
