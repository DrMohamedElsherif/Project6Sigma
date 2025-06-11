# config.py
import os
from dotenv import load_dotenv
from functools import lru_cache


class Settings:
    def __init__(self):
        load_dotenv()
        self.staticFilePath = os.environ.get("staticFilePath")
        self.staticUrl = os.environ.get("staticUrl")
        self.useFullPath = os.environ.get("useFullPath")
        self.azureEndpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.azureApiKey = os.environ.get("AZURE_OPENAI_API_KEY")
        self.azureModel = os.environ.get("AZURE_OPENAI_MODEL")


@lru_cache()
def get_settings():
    return Settings()


# Verwendung bleibt gleich:
settings = get_settings()
