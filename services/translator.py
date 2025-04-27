"""
Translator service chain implementation.
Implements a multi-provider API chain (DeepL → Gemini → OpenAI) with fallback logic.
"""
import os
import json
import requests
from typing import Dict, Optional, Union, Any
import logging
import google.generativeai as genai
from openai import OpenAI
import deepl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

class BaseTranslator:
    """Base class for all translator providers"""
    name = "base"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                 tone: str = "default") -> str:
        """
        Translate text from source language to target language
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            source_lang (Optional[str]): Source language code or None for auto-detection
            tone (str): Formal or informal tone
            
        Returns:
            str: Translated text
            
        Raises:
            TranslationError: If translation fails
        """
        raise NotImplementedError("Subclasses must implement translate()")
    
    def is_available(self) -> bool:
        """Check if this translator is available (has valid API key)"""
        return bool(self.api_key)

class DeepLTranslator(BaseTranslator):
    """DeepL API integration using the official Python library"""
    name = "deepl"
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.client = None
        if api_key:
            try:
                self.client = deepl.Translator(api_key)
            except Exception as e:
                logger.error(f"Failed to initialize DeepL client: {e}")
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                 tone: str = "default") -> str:
        """Translate text using DeepL API"""
        if not self.is_available() or not self.client:
            raise TranslationError("DeepL API key not available or client initialization failed")
        
        try:
            # Map tone to DeepL formality parameter
            formality = None
            if tone.lower() == "formal":
                formality = "prefer_more"
            elif tone.lower() == "informal":
                formality = "prefer_less"
            
            # Convert language codes to DeepL format
            target_lang_code = self._normalize_lang_code(target_lang)
            source_lang_code = self._normalize_lang_code(source_lang) if source_lang else None
            
            # Make API call with the DeepL library
            result = self.client.translate_text(
                text=text,
                target_lang=target_lang_code,
                source_lang=source_lang_code,
                formality=formality
            )
            
            # Return the translated text
            return result.text
            
        except deepl.exceptions.DeepLException as e:
            logger.error(f"DeepL API error: {e}")
            raise TranslationError(f"DeepL translation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected DeepL error: {e}")
            raise TranslationError(f"DeepL translation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if DeepL translator is available"""
        return bool(self.api_key) and bool(self.client)
    
    def _normalize_lang_code(self, lang_code: str) -> str:
        """Convert language codes to DeepL format"""
        if not lang_code:
            return None
            
        # DeepL uses uppercase two-letter codes
        if len(lang_code) == 2:
            return lang_code.upper()
        
        # DeepL uses specific format for variants like EN-US
        if "-" in lang_code:
            base, variant = lang_code.split("-", 1)
            return f"{base.upper()}-{variant.upper()}"
        
        return lang_code.upper()

class GeminiTranslator(BaseTranslator):
    """Google Gemini API integration"""
    name = "gemini"
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        if api_key:
            genai.configure(api_key=api_key)
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                 tone: str = "default") -> str:
        """Translate text using Google Gemini API"""
        if not self.is_available():
            raise TranslationError("Gemini API key not available")
        
        try:
            # Configure the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create prompt with instructions
            prompt = f"Translate the following text"
            
            if source_lang:
                prompt += f" from {self._get_language_name(source_lang)}"
                
            prompt += f" to {self._get_language_name(target_lang)}"
            
            if tone.lower() in ["formal", "informal"]:
                prompt += f" using {tone} tone"
                
            prompt += f":\n\n{text}\n\nTranslation:"
            
            # Generate translation
            response = model.generate_content(prompt)
            
            # Extract and return the translated text
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise TranslationError(f"Gemini translation failed: {str(e)}")
    
    def _get_language_name(self, lang_code: str) -> str:
        """Convert language code to full language name"""
        lang_map = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "zh": "Chinese",
            "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
            "nl": "Dutch", "pl": "Polish", "tr": "Turkish"
        }
        
        base_code = lang_code.split("-")[0].lower()
        return lang_map.get(base_code, lang_code)

class OpenAITranslator(BaseTranslator):
    """OpenAI API integration"""
    name = "openai"
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.client = None
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                 tone: str = "default") -> str:
        """Translate text using OpenAI API"""
        if not self.is_available():
            raise TranslationError("OpenAI API key not available")
        
        try:
            # Create system instruction
            system_prompt = "You are a professional translator. Translate text accurately while preserving meaning."
            
            # Create user prompt with instructions
            user_prompt = f"Translate the following text"
            
            if source_lang:
                user_prompt += f" from {self._get_language_name(source_lang)}"
                
            user_prompt += f" to {self._get_language_name(target_lang)}"
            
            if tone.lower() in ["formal", "informal"]:
                user_prompt += f" using {tone} tone"
                
            user_prompt += f":\n\n{text}"
            
            # Make API call
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096,
                temperature=0.1
            )
            
            # Extract and return the translated text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise TranslationError(f"OpenAI translation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI translator is available"""
        return bool(self.api_key) and bool(self.client)
    
    def _get_language_name(self, lang_code: str) -> str:
        """Convert language code to full language name"""
        lang_map = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "zh": "Chinese",
            "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
            "nl": "Dutch", "pl": "Polish", "tr": "Turkish"
        }
        
        base_code = lang_code.split("-")[0].lower()
        return lang_map.get(base_code, lang_code)

class TranslatorService:
    """
    Main translator service that manages multiple providers and implements
    the fallback chain logic.
    """
    def __init__(self):
        self.providers = []
    
    def add_provider(self, provider: BaseTranslator) -> None:
        """Add a translation provider to the service chain"""
        self.providers.append(provider)
    
    def setup_providers(self, deepl_key: Optional[str] = None, 
                      gemini_key: Optional[str] = None,
                      openai_key: Optional[str] = None) -> None:
        """
        Set up all supported providers with available API keys
        """
        # Clear existing providers
        self.providers = []
        
        # Set up providers in order of preference
        if deepl_key:
            self.add_provider(DeepLTranslator(deepl_key))
        if gemini_key:
            self.add_provider(GeminiTranslator(gemini_key))
        if openai_key:
            self.add_provider(OpenAITranslator(openai_key))
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                tone: str = "default") -> Dict[str, str]:
        """
        Translate text using the provider chain with fallback logic
        
        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code or None for auto-detect
            tone: Formal or informal tone
            
        Returns:
            dict: {
                "translation": translated text,
                "provider": name of provider used,
                "error": error message if all providers failed
            }
        """
        if not self.providers:
            return {
                "translation": "",
                "provider": None,
                "error": "No translation providers available"
            }
        
        # Try each provider in sequence until one succeeds
        errors = []
        for provider in self.providers:
            try:
                translation = provider.translate(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    tone=tone
                )
                
                # Return successful result
                return {
                    "translation": translation,
                    "provider": provider.name,
                    "error": None
                }
                
            except TranslationError as e:
                # Log error and continue to next provider
                logger.warning(f"{provider.name} translation failed: {str(e)}")
                errors.append(f"{provider.name}: {str(e)}")
        
        # If we get here, all providers failed
        error_message = "All translation providers failed: " + "; ".join(errors)
        logger.error(error_message)
        
        return {
            "translation": "",
            "provider": None,
            "error": error_message
        }

def smart_translate(text: str, target_lang: str, source_lang: Optional[str] = None,
                  tone: str = "default", deepl_key: Optional[str] = None,
                  gemini_key: Optional[str] = None, openai_key: Optional[str] = None) -> Dict[str, str]:
    """
    Main function to translate text using available providers
    
    Args:
        text: Text to translate
        target_lang: Target language code
        source_lang: Source language code or None for auto-detect
        tone: Formal or informal tone
        deepl_key: DeepL API key
        gemini_key: Google Gemini API key
        openai_key: OpenAI API key
    
    Returns:
        dict: {
            "translation": translated text,
            "provider": name of provider used
        }
    """
    # Create service and set up providers
    service = TranslatorService()
    service.setup_providers(
        deepl_key=deepl_key,
        gemini_key=gemini_key,
        openai_key=openai_key
    )
    
    # Perform translation
    result = service.translate(
        text=text,
        target_lang=target_lang,
        source_lang=source_lang,
        tone=tone
    )
    
    return result