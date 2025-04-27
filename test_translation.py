"""
Manual test script for the translator service.
This script tests the translator service with the provided API keys.
"""
import os
import dotenv
from services.translator import smart_translate

# Load environment variables from .env file
dotenv.load_dotenv()

def test_translation():
    """Test translation with all available providers"""
    
    # Get API keys from environment variables
    deepl_key = os.getenv("DEEPL_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"DeepL API key available: {bool(deepl_key)}")
    print(f"Gemini API key available: {bool(gemini_key)}")
    print(f"OpenAI API key available: {bool(openai_key)}")
    
    # Text to translate
    text = "Hello world! This is a test of the translation service."
    
    print("\nTesting translation to Spanish...")
    result = smart_translate(
        text=text,
        target_lang="es",
        source_lang="en",
        tone="formal",
        deepl_key=deepl_key,
        gemini_key=gemini_key,
        openai_key=openai_key
    )
    
    print(f"\nTranslation result:")
    print(f"Provider used: {result['provider']}")
    print(f"Translation: {result['translation']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    # Test fallback mechanism by using an invalid DeepL key
    print("\nTesting fallback mechanism (invalid DeepL key)...")
    result = smart_translate(
        text=text,
        target_lang="es",
        source_lang="en",
        tone="formal",
        deepl_key="invalid_key",
        gemini_key=gemini_key,
        openai_key=openai_key
    )
    
    print(f"\nFallback result:")
    print(f"Provider used: {result['provider']}")
    print(f"Translation: {result['translation']}")
    if result.get("error"):
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_translation()