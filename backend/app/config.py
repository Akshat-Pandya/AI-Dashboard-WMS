import os
from dotenv import load_dotenv

load_dotenv()  # loads from project root

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("MODEL_NAME")