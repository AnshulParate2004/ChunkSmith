import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv


async def check_key(name: str, api_key: str):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content("hello")
        )

        print(f"[VALID] {name} works")
        return True

    except Exception as e:
        print(f"[INVALID] {name} failed → {str(e)[:120]}")
        return False


async def main():
    load_dotenv()

    key_names = [
        "GOOGLE_API_KEY",     # base key
        "GOOGLE_API_KEY_1",
        "GOOGLE_API_KEY_2",
        "GOOGLE_API_KEY_3",
        "GOOGLE_API_KEY_4",
        "GOOGLE_API_KEY_5",
        "GOOGLE_API_KEY_6",
        "GOOGLE_API_KEY_7",
        "GOOGLE_API_KEY_8",
        "GOOGLE_API_KEY_9",
        "GOOGLE_API_KEY_10",
        "GOOGLE_API_KEY_11",
    ]

    tasks = []
    for name in key_names:
        key = os.getenv(name)
        if key:
            tasks.append(check_key(name, key))
        else:
            print(f"[SKIPPED] {name} not found in .env")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
