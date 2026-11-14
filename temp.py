
import os
from google import genai

# Configure your API key
API_KEY = "123456"

try:
    # Initialize Gemini client
    client = genai.Client(api_key=API_KEY)

    print("Connecting to Gemini...")

    # Send a test request
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Hello Gemini! Reply with 'Connection successful'."
    )

    # Print response
    print("\nSUCCESS! Gemini API is working.")
    print("Model response:", response.text)

except Exception as e:
    print("\nFAILED! Could not connect to Gemini.")
    print("Error:", str(e))
