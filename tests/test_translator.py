"""
Tests for the translator service chain.
Uses mock responses to test the functionality of the API chain.
"""
import pytest
import unittest.mock as mock
import json
import requests
from typing import Dict, Any, Optional

# Import the modules to test
from services.translator import (
    TranslatorService, DeepLTranslator, GeminiTranslator, OpenAITranslator,
    BaseTranslator, TranslationError, smart_translate
)

class MockResponse:
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data
        self.text = json.dumps(json_data)
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


class TestBaseTranslator:
    """Tests for the BaseTranslator class"""
    
    def test_is_available(self):
        """Test the is_available method"""
        translator = BaseTranslator()
        assert not translator.is_available()
        
        translator = BaseTranslator(api_key="test-key")
        assert translator.is_available()
    
    def test_translate_not_implemented(self):
        """Test that translate() raises NotImplementedError"""
        translator = BaseTranslator(api_key="test-key")
        with pytest.raises(NotImplementedError):
            translator.translate("test", "en")


class TestDeepLTranslator:
    """Tests for the DeepLTranslator class"""
    
    def test_normalize_lang_code(self):
        """Test language code normalization"""
        translator = DeepLTranslator(api_key="test-key")
        
        assert translator._normalize_lang_code("en") == "EN"
        assert translator._normalize_lang_code("en-us") == "EN-US"
        assert translator._normalize_lang_code("EN-gb") == "EN-GB"
    
    @mock.patch('requests.post')
    def test_translate_success(self, mock_post):
        """Test successful translation using DeepL"""
        # Set up mock response
        mock_response = MockResponse(200, {
            "translations": [
                {"text": "Hola mundo"}
            ]
        })
        mock_post.return_value = mock_response
        
        # Create translator and call translate
        translator = DeepLTranslator(api_key="test-key")
        result = translator.translate("Hello world", "es")
        
        # Verify result
        assert result == "Hola mundo"
        
        # Verify API was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs['headers']['Authorization'] == "DeepL-Auth-Key test-key"
        assert kwargs['json']['text'] == ["Hello world"]
        assert kwargs['json']['target_lang'] == "ES"
    
    @mock.patch('requests.post')
    def test_translate_with_source_and_tone(self, mock_post):
        """Test translation with source language and tone"""
        # Set up mock response
        mock_response = MockResponse(200, {
            "translations": [
                {"text": "Bonjour le monde"}
            ]
        })
        mock_post.return_value = mock_response
        
        # Create translator and call translate
        translator = DeepLTranslator(api_key="test-key")
        result = translator.translate("Hello world", "fr", "en", "formal")
        
        # Verify API was called with correct parameters
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs['json']['source_lang'] == "EN"
        assert kwargs['json']['formality'] == "more"
    
    @mock.patch('requests.post')
    def test_translate_error(self, mock_post):
        """Test error handling for DeepL API"""
        # Set up mock error response
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        # Create translator and verify error handling
        translator = DeepLTranslator(api_key="test-key")
        with pytest.raises(TranslationError) as excinfo:
            translator.translate("Hello world", "es")
            
        assert "DeepL translation failed" in str(excinfo.value)


class TestGeminiTranslator:
    """Tests for the GeminiTranslator class"""
    
    def test_get_language_name(self):
        """Test language code to name conversion"""
        translator = GeminiTranslator(api_key="test-key")
        
        assert translator._get_language_name("en") == "English"
        assert translator._get_language_name("es-mx") == "Spanish"
        assert translator._get_language_name("unknown") == "unknown"
    
    @mock.patch('google.generativeai.GenerativeModel')
    def test_translate_success(self, mock_model_class):
        """Test successful translation using Gemini"""
        # Set up mock response
        mock_model = mock.MagicMock()
        mock_model_class.return_value = mock_model
        mock_response = mock.MagicMock()
        mock_response.text = "Hola mundo"
        mock_model.generate_content.return_value = mock_response
        
        # Create translator and call translate
        translator = GeminiTranslator(api_key="test-key")
        result = translator.translate("Hello world", "es")
        
        # Verify result
        assert result == "Hola mundo"
        
        # Verify API was called with correct parameters
        mock_model.generate_content.assert_called_once()
        args, _ = mock_model.generate_content.call_args
        assert "Hello world" in args[0]
        assert "Spanish" in args[0]
    
    @mock.patch('google.generativeai.GenerativeModel')
    def test_translate_error(self, mock_model_class):
        """Test error handling for Gemini API"""
        # Set up mock error
        mock_model = mock.MagicMock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        # Create translator and verify error handling
        translator = GeminiTranslator(api_key="test-key")
        with pytest.raises(TranslationError) as excinfo:
            translator.translate("Hello world", "es")
            
        assert "Gemini translation failed" in str(excinfo.value)


class TestOpenAITranslator:
    """Tests for the OpenAITranslator class"""
    
    @mock.patch('openai.OpenAI')
    def test_translate_success(self, mock_openai_class):
        """Test successful translation using OpenAI"""
        # Set up mock response
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_choice = mock.MagicMock()
        mock_message = mock.MagicMock()
        mock_message.content = "Hola mundo"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create translator and call translate
        translator = OpenAITranslator(api_key="test-key")
        result = translator.translate("Hello world", "es")
        
        # Verify result
        assert result == "Hola mundo"
        
        # Verify API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs['model'] == "gpt-4"
        assert len(kwargs['messages']) == 2
        assert "Spanish" in kwargs['messages'][1]['content']
    
    @mock.patch('openai.OpenAI')
    def test_translate_error(self, mock_openai_class):
        """Test error handling for OpenAI API"""
        # Set up mock error
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Create translator and verify error handling
        translator = OpenAITranslator(api_key="test-key")
        with pytest.raises(TranslationError) as excinfo:
            translator.translate("Hello world", "es")
            
        assert "OpenAI translation failed" in str(excinfo.value)


class TestTranslatorService:
    """Tests for the TranslatorService class"""
    
    def test_add_provider(self):
        """Test adding providers"""
        service = TranslatorService()
        provider = BaseTranslator(api_key="test-key")
        service.add_provider(provider)
        assert len(service.providers) == 1
        assert service.providers[0] == provider
    
    def test_setup_providers(self):
        """Test setting up providers with API keys"""
        service = TranslatorService()
        service.setup_providers(
            deepl_key="deepl-key",
            gemini_key="gemini-key",
            openai_key="openai-key"
        )
        
        assert len(service.providers) == 3
        assert isinstance(service.providers[0], DeepLTranslator)
        assert isinstance(service.providers[1], GeminiTranslator)
        assert isinstance(service.providers[2], OpenAITranslator)
        
        # Test with partial keys
        service.setup_providers(deepl_key="deepl-key")
        assert len(service.providers) == 1
        assert isinstance(service.providers[0], DeepLTranslator)
    
    def test_translate_no_providers(self):
        """Test translation with no providers"""
        service = TranslatorService()
        result = service.translate("Hello world", "es")
        
        assert result["translation"] == ""
        assert result["provider"] is None
        assert "No translation providers available" in result["error"]
    
    def test_translate_success(self):
        """Test successful translation with first provider"""
        service = TranslatorService()
        
        # Create mock provider
        mock_provider = mock.MagicMock()
        mock_provider.name = "mock-provider"
        mock_provider.translate.return_value = "Hola mundo"
        
        # Add provider and translate
        service.add_provider(mock_provider)
        result = service.translate("Hello world", "es")
        
        assert result["translation"] == "Hola mundo"
        assert result["provider"] == "mock-provider"
        assert result["error"] is None
        
        # Verify provider was called with correct parameters
        mock_provider.translate.assert_called_once_with(
            text="Hello world",
            target_lang="es",
            source_lang=None,
            tone="default"
        )
    
    def test_translate_fallback(self):
        """Test fallback to second provider when first fails"""
        service = TranslatorService()
        
        # Create mock providers
        mock_provider1 = mock.MagicMock()
        mock_provider1.name = "provider1"
        mock_provider1.translate.side_effect = TranslationError("Provider 1 error")
        
        mock_provider2 = mock.MagicMock()
        mock_provider2.name = "provider2"
        mock_provider2.translate.return_value = "Hola mundo"
        
        # Add providers and translate
        service.add_provider(mock_provider1)
        service.add_provider(mock_provider2)
        result = service.translate("Hello world", "es")
        
        # Verify result used second provider
        assert result["translation"] == "Hola mundo"
        assert result["provider"] == "provider2"
        assert result["error"] is None
        
        # Verify both providers were called
        mock_provider1.translate.assert_called_once()
        mock_provider2.translate.assert_called_once()
    
    def test_translate_all_providers_fail(self):
        """Test handling when all providers fail"""
        service = TranslatorService()
        
        # Create mock providers that all fail
        mock_provider1 = mock.MagicMock()
        mock_provider1.name = "provider1"
        mock_provider1.translate.side_effect = TranslationError("Provider 1 error")
        
        mock_provider2 = mock.MagicMock()
        mock_provider2.name = "provider2"
        mock_provider2.translate.side_effect = TranslationError("Provider 2 error")
        
        # Add providers and translate
        service.add_provider(mock_provider1)
        service.add_provider(mock_provider2)
        result = service.translate("Hello world", "es")
        
        # Verify error result
        assert result["translation"] == ""
        assert result["provider"] is None
        assert "All translation providers failed" in result["error"]
        assert "provider1" in result["error"]
        assert "provider2" in result["error"]


class TestSmartTranslate:
    """Tests for the smart_translate function"""
    
    @mock.patch('services.translator.TranslatorService')
    def test_smart_translate(self, mock_service_class):
        """Test smart_translate function"""
        # Set up mock service
        mock_service = mock.MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.translate.return_value = {
            "translation": "Hola mundo",
            "provider": "deepl",
            "error": None
        }
        
        # Call smart_translate
        result = smart_translate(
            text="Hello world",
            target_lang="es",
            source_lang="en",
            tone="formal",
            deepl_key="deepl-key",
            gemini_key="gemini-key",
            openai_key="openai-key"
        )
        
        # Verify result
        assert result["translation"] == "Hola mundo"
        assert result["provider"] == "deepl"
        
        # Verify service was set up and called correctly
        mock_service.setup_providers.assert_called_once_with(
            deepl_key="deepl-key",
            gemini_key="gemini-key",
            openai_key="openai-key"
        )
        
        mock_service.translate.assert_called_once_with(
            text="Hello world",
            target_lang="es",
            source_lang="en",
            tone="formal"
        )