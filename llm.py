import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("base_url"),
    api_key=os.environ.get("api_key"),
)