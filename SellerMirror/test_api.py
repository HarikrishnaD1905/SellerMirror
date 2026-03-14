import os
from dotenv import load_dotenv  # type: ignore
from mistralai.client import Mistral  # type: ignore

# Force load exactly from the given path
env_path = r"c:\Users\Harikrishna\Desktop\SellerMirror\.env"
load_dotenv(dotenv_path=env_path, override=True)

key = os.getenv('MISTRAL_API_KEY')
if not key:
    print("NO KEY FOUND IN .ENV!")
    exit(1)

key = str(key)
print(f"Loaded key starting with: {key[:10]}... (length {len(key)})")  # type: ignore

models = ["mistral-small-latest"]
for m in models:
    try:
        print(f"Testing {m}...")
        client = Mistral(api_key=key)
        response = client.chat.complete(
            model=m,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ]
        )
        print(f"API SUCCESS with {m}! Response: {response.choices[0].message.content[:20]}")  # type: ignore
    except Exception as e:
        print(f"API ERROR for {m}: {e}")
