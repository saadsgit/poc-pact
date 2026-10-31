"""Application configuration."""

from pathlib import Path

APP_NAME = "POC Pact"
MODEL_ID = "gemma-4-26b-a4b-it"
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATABASE_PATH = DATA_DIR / "poc_pact.db"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_NOTES_CHARS = 5_000

CURRENCIES = ("USD", "SGD", "MYR", "IDR", "THB", "VND", "PHP", "BND")
OUTCOME_TYPES = (
    "",
    "POC launched",
    "Commercial partnership",
    "Investment",
    "Market expansion",
    "Cross-border sale",
    "Other",
)

STATUSES = (
    "Captured",
    "Follow-up sent",
    "Meeting booked",
    "POC proposed",
    "POC agreed",
    "POC running",
    "Outcome recorded",
    "Closed",
)

ASEAN_COUNTRIES = (
    "Brunei",
    "Cambodia",
    "Indonesia",
    "Laos",
    "Malaysia",
    "Myanmar",
    "Philippines",
    "Singapore",
    "Thailand",
    "Vietnam",
    "Other / not specified",
)
