import os
import asyncio
from groq import Groq
from dotenv import load_dotenv


async def check_key(name: str, api_key: str):
    try:
        # Groq client
        client = Groq(api_key=api_key)

        loop = asyncio.get_event_loop()
        # Run blocking call in executor thread
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "hello"}]
            )
        )

        print(f"[VALID] {name} works")
        return True

    except Exception as e:
        print(f"[INVALID] {name} failed → {str(e)[:80]}")
        return False


async def main():
    load_dotenv()

    key_names = [
        "GROQ_API_KEY_1",
        "GROQ_API_KEY_2",
        "GROQ_API_KEY_3",
        "GROQ_API_KEY_4",
        "GROQ_API_KEY_5",
        "GROQ_API_KEY_6",
        "GROQ_API_KEY_7",
        "GROQ_API_KEY_8",
        "GROQ_API_KEY_9",
        "GROQ_API_KEY_10",
        "GROQ_API_KEY_11",
    ]

    tasks = []
    for name in key_names:
        key = os.getenv(name)
        if key:
            tasks.append(check_key(name, key))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
