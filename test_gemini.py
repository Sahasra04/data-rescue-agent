import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads .env file and loads GEMINI_API_KEY into environment

def main():
    ...
def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set the GEMINI_API_KEY environment variable first.")
        return

    client = genai.Client(api_key=api_key)

    prompt = "In one sentence, explain what a 'data rescue agent' could do with a messy spreadsheet."

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    print("=== Gemini responded ===")
    print(response.text)
    print("=========================")

if __name__ == "__main__":
    main()