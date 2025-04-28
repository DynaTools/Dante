"""
Translator service chain implementation.
Implements a multi-provider API chain (DeepL → Gemini → OpenAI) with fallback logic.
"""
import os
import json
import requests
from typing import Dict, Optional, Union, Any, List, Tuple
import logging
import google.generativeai as genai
from openai import OpenAI
import deepl
import time
from utils.cache import TranslationCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the global translation cache
translation_cache = TranslationCache(max_size=100, ttl=3600)

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
            
            # Create prompt with direct, clear instructions
            prompt = "Translate the text below"
            
            if source_lang:
                prompt += f" from {self._get_language_name(source_lang)}"
                
            prompt += f" to {self._get_language_name(target_lang)}"
            
            if tone.lower() in ["formal", "informal"]:
                prompt += f" using {tone} tone"
                
            prompt += ". Respond with ONLY the translation, no explanations, prefixes, or additional text. Here's the text to translate:\n\n"
            prompt += text
            
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
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key)
        self.client = None
        self.model = model
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                 tone: str = "default") -> str:
        """Translate text using OpenAI API"""
        if not self.is_available():
            raise TranslationError("OpenAI API key not available")
        
        try:
            # Create system instruction with clear guidance to avoid typical AI patterns
            system_prompt = ("You are a translation tool that provides only direct translations with no explanations, "
                           "no introductory text, no notes, and no AI tendencies like 'Sure, I'll translate that' or " 
                           "'Here's the translation'. Return only the translated text itself.")
            
            # Create user prompt with instructions
            user_prompt = f"Translate this text"
            
            if source_lang:
                user_prompt += f" from {self._get_language_name(source_lang)}"
                
            user_prompt += f" to {self._get_language_name(target_lang)}"
            
            if tone.lower() in ["formal", "informal"]:
                user_prompt += f" using {tone} tone"
                
            user_prompt += f":\n\n{text}"
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
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
                tone: str = "default", retry_count: int = 2) -> Dict[str, str]:
        """
        Translate text using the provider chain with fallback logic
        
        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code or None for auto-detect
            tone: Formal or informal tone
            retry_count: Number of retry attempts for each provider
            
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
            for attempt in range(retry_count + 1):
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
                    logger.warning(f"{provider.name} translation failed on attempt {attempt + 1}: {str(e)}")
                    errors.append(f"{provider.name} (attempt {attempt + 1}): {str(e)}")
                    time.sleep(1)  # Optional: wait before retrying
        
        # If we get here, all providers failed
        error_message = "All translation providers failed: " + "; ".join(errors)
        logger.error(error_message)
        
        return {
            "translation": "",
            "provider": None,
            "error": error_message
        }

# Add a helper function to detect language (approximate method)
def detect_language(text: str) -> str:
    """
    Basic language detection for common languages.
    This is a simplified method - in production, use a proper language detection library
    """
    # Common words/patterns for some languages
    patterns = {
        "en": ["the", "and", "is", "in", "to", "of", "that", "for", "with", "as"],
        "es": ["el", "la", "los", "las", "es", "en", "de", "que", "por", "con", "para"],
        "fr": ["le", "la", "les", "est", "en", "de", "que", "pour", "avec", "comme"],
        "pt": ["o", "a", "os", "as", "é", "em", "de", "que", "por", "com", "para"],
        "de": ["der", "die", "das", "ist", "in", "zu", "mit", "für", "und", "von"],
        "it": ["il", "la", "le", "è", "in", "di", "che", "per", "con", "come"],
    }
    
    text = text.lower()
    words = text.split()
    scores = {}
    
    for lang, common_words in patterns.items():
        count = sum(1 for word in words if word in common_words)
        if words:
            scores[lang] = count / len(words)
    
    if not scores:
        return "en"  # Default to English if no match
    
    # Get language with highest score
    detected_lang = max(scores.items(), key=lambda x: x[1])
    
    # Only return if confidence is reasonable
    if detected_lang[1] > 0.1:
        return detected_lang[0]
    return "en"  # Default to English

def smart_translate(text: str, target_lang: str, source_lang: Optional[str] = None,
                  tone: str = "default", deepl_key: Optional[str] = None,
                  gemini_key: Optional[str] = None, openai_key: Optional[str] = None,
                  use_cache: bool = True, retry_count: int = 1) -> Dict[str, Any]:
    """
    Main function to translate text using available providers with caching and retry
    
    Args:
        text: Text to translate
        target_lang: Target language code
        source_lang: Source language code or None for auto-detect
        tone: Formal or informal tone
        deepl_key: DeepL API key
        gemini_key: Google Gemini API key
        openai_key: OpenAI API key
        use_cache: Whether to use the translation cache
        retry_count: Number of retry attempts for each provider
    
    Returns:
        dict: {
            "translation": translated text,
            "provider": name of provider used,
            "error": error message if all providers failed
        }
    """
    # Check if translation is in cache
    if use_cache:
        cached_result = translation_cache.get_translation(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            tone=tone
        )
        if cached_result:
            logger.info(f"Using cached translation from {cached_result['provider']}")
            return cached_result
    
    # Otimização: Se apenas uma API key estiver disponível, podemos ir direto para esse provedor
    # sem a necessidade de configurar todos os outros
    
    # Check if only one provider key is available
    available_keys = [k for k in [deepl_key, gemini_key, openai_key] if k]
    if len(available_keys) == 1:
        # Single provider path - faster execution
        if deepl_key:
            try:
                logger.info("Using direct DeepL translation path")
                translator = DeepLTranslator(deepl_key)
                translation = translator.translate(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    tone=tone
                )
                result = {
                    "translation": translation,
                    "provider": "deepl",
                    "error": None
                }
            except Exception as e:
                logger.error(f"DeepL translation failed: {e}")
                result = {
                    "translation": "",
                    "provider": None,
                    "error": f"DeepL translation failed: {str(e)}"
                }
        elif gemini_key:
            try:
                logger.info("Using direct Gemini translation path")
                translator = GeminiTranslator(gemini_key)
                translation = translator.translate(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    tone=tone
                )
                result = {
                    "translation": translation,
                    "provider": "gemini",
                    "error": None
                }
            except Exception as e:
                logger.error(f"Gemini translation failed: {e}")
                result = {
                    "translation": "",
                    "provider": None,
                    "error": f"Gemini translation failed: {str(e)}"
                }
        elif openai_key:
            try:
                logger.info("Using direct OpenAI translation path")
                translator = OpenAITranslator(openai_key)
                translation = translator.translate(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    tone=tone
                )
                result = {
                    "translation": translation,
                    "provider": "openai",
                    "error": None
                }
            except Exception as e:
                logger.error(f"OpenAI translation failed: {e}")
                result = {
                    "translation": "",
                    "provider": None,
                    "error": f"OpenAI translation failed: {str(e)}"
                }
        else:
            result = {
                "translation": "",
                "provider": None,
                "error": "No translation providers available"
            }
    else:
        # Multiple providers available, use the fallback chain
        # Create service and set up providers
        service = TranslatorService()
        service.setup_providers(
            deepl_key=deepl_key,
            gemini_key=gemini_key,
            openai_key=openai_key
        )
        
        # Perform translation with retries
        result = service.translate(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            tone=tone,
            retry_count=retry_count
        )
    
    # Cache the successful translation
    if use_cache and result["translation"] and not result["error"]:
        translation_cache.cache_translation(
            text=text,
            result=result,
            target_lang=target_lang,
            source_lang=source_lang,
            tone=tone
        )
    
    return result