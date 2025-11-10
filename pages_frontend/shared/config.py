# app/core/config.py

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
        
    API_KEY: str = os.getenv("API_KEY")
    ALTHEIA_BACKEND: str = os.getenv("ALTHEIA_BACKEND")

settings = Settings()
