import os
import logging

# Define the base directory for solutions
SOLUTIONS_DIR = "solutions"


def load_local_solution(platform, identifier):
    """Loads a solution from the local filesystem cache."""
    path = os.path.join(SOLUTIONS_DIR, platform, f"{identifier}.cpp")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                logging.info(f"Loaded local solution for {platform}/{identifier}")
                return f.read(), True
        except IOError as e:
            logging.error(f"Error reading local solution file {path}: {e}")
            return None, False
    return None, False


def save_solution(platform, identifier, code):
    """Saves a generated solution to the local filesystem cache."""
    path = os.path.join(SOLUTIONS_DIR, platform, f"{identifier}.cpp")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        logging.info(f"Saved solution to {path}")
    except IOError as e:
        logging.error(f"Error saving solution file {path}: {e}")
