# config.py
# Purpose: load settings from .env and expose them to the rest of the app.
# No other file should read .env or os.environ directly.

import os
from dotenv import load_dotenv

CONFIG_FOLDER = os.path.dirname(os.path.abspath(__file__))
BACKEND_FOLDER = os.path.dirname(CONFIG_FOLDER)
ENV_FILE_PATH = os.path.join(BACKEND_FOLDER, ".env")

# override=True: values in .env win over same-named Windows variables.
load_dotenv(ENV_FILE_PATH, override=True)


def get_text_setting(setting_name, default_value=""):
    """Read a text setting. Return default_value if missing."""
    value = os.getenv(setting_name, default_value)
    return value.strip()


def get_number_setting(setting_name, default_value):
    """Read a whole-number setting. Return default_value if missing/invalid."""
    raw_value = os.getenv(setting_name, "")
    try:
        return int(raw_value)
    except ValueError:
        return default_value

def get_float_setting(setting_name, default_value):
    """Read a decimal-number setting. Return default if missing or invalid."""
    raw_value = os.getenv(setting_name, "")
    try:
        return float(raw_value)
    except ValueError:
        return default_value

    
# ---------------- SQL Server settings ----------------
DB_SERVER = get_text_setting("DB_SERVER")
DB_NAME = get_text_setting("DB_NAME")
DB_USER = get_text_setting("DB_USER")
DB_PASSWORD = get_text_setting("DB_PASSWORD")
DB_DRIVER = get_text_setting("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_TRUST_SERVER_CERTIFICATE = get_text_setting("DB_TRUST_SERVER_CERTIFICATE", "yes")

# ---------------- Query safety limits ----------------
QUERY_TIMEOUT_SECONDS = get_number_setting("QUERY_TIMEOUT_SECONDS", 30)
MAX_ROWS_RETURNED = get_number_setting("MAX_ROWS_RETURNED", 500)
SCHEMA_CACHE_MINUTES = get_number_setting("SCHEMA_CACHE_MINUTES", 60)

# ---------------- Gemini settings (used in Phase 4) ----------------
GOOGLE_API_KEY = get_text_setting("GOOGLE_API_KEY")
GEMINI_MODEL = get_text_setting("GEMINI_MODEL")
GEMINI_TEMPERATURE = get_float_setting("GEMINI_TEMPERATURE", 0.0)
GEMINI_TIMEOUT_SECONDS = get_number_setting("GEMINI_TIMEOUT_SECONDS", 60)

# ---------------- Paths ----------------
DATA_FOLDER = os.path.join(BACKEND_FOLDER, "data")
CONVERSATION_DB_PATH = os.path.join(DATA_FOLDER, "conversations.db")


def get_missing_database_settings():
    """Return a list of required DB settings that are empty."""
    required_settings = {
        "DB_SERVER": DB_SERVER,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
    }
    missing_names = []
    for setting_name, setting_value in required_settings.items():
        if setting_value == "":
            missing_names.append(setting_name)
    return missing_names