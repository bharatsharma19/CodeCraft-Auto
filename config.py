# config.py
import os
from dotenv import load_dotenv
import logging

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
MODEL_NAME = "gpt-4"  # Or "gpt-3.5-turbo"
USE_GEMINI = True  # Set True to use Gemini instead of OpenAI

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")  # If using Gemini

# Email configuration for notifications
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# LeetCode login credentials
LEETCODE_USERNAME = os.getenv("LEETCODE_USERNAME", "your-leetcode-username")
LEETCODE_PASSWORD = os.getenv("LEETCODE_PASSWORD", "your-leetcode-password")

# Global AI client instances
import openai

openai_client = None
gemini_model = None


def initialize_ai_clients():
    """Initialize OpenAI and Gemini clients once"""
    global openai_client, gemini_model

    if not USE_GEMINI and OPENAI_API_KEY != "your-openai-api-key":
        try:
            openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logging.info("OpenAI client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")

    if USE_GEMINI and GEMINI_API_KEY != "your-gemini-api-key":
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel("gemini-2.5-pro")
            logging.info("Gemini client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini client: {e}")


# Initialize clients on module import
initialize_ai_clients()


# Check if API keys are properly configured
def check_api_keys():
    if USE_GEMINI:
        if GEMINI_API_KEY == "your-gemini-api-key":
            logging.warning(
                "GEMINI_API_KEY not set. Please set it as an environment variable."
            )
            return False
        return True
    else:
        if OPENAI_API_KEY == "your-openai-api-key":
            logging.warning(
                "OPENAI_API_KEY not set. Please set it as an environment variable."
            )
            return False
        return True


def check_email_config():
    if EMAIL_ADDRESS == "your-email@gmail.com" or EMAIL_PASSWORD == "your-app-password":
        logging.warning(
            "Email configuration not set. Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."
        )
        return False
    return True


def check_leetcode_config():
    if (
        LEETCODE_USERNAME == "your-leetcode-username"
        or LEETCODE_PASSWORD == "your-leetcode-password"
    ):
        logging.warning(
            "LeetCode credentials not set. Please set LEETCODE_USERNAME and LEETCODE_PASSWORD environment variables."
        )
        return False
    return True
