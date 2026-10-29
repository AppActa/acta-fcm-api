from os import getenv

from dotenv import load_dotenv

load_dotenv()

DB_URL = getenv('DB_URL')
ACTA_AUTH_API_URL = getenv('ACTA_AUTH_API_URL')
INTERNAL_API_TOKEN = getenv('INTERNAL_API_TOKEN')
FIREBASE_PROJECT_ID = getenv('FIREBASE_PROJECT_ID')