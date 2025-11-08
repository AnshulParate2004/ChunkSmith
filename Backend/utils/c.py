import os
from dotenv import load_dotenv

# Load the .env file (adjust path if needed)
load_dotenv(r"D:\MultiModulRag\.env")

# Now access the variable
print(os.getenv("HF_TOKEN"))
