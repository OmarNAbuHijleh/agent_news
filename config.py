# configuration for our python code. Relevant information is retrieved from our ".env" file
import os
from dotenv import load_dotenv


load_dotenv()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
