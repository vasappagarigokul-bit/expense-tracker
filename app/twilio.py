from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE):
    raise ValueError(
        "Server Misconfiguration."
    )

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)