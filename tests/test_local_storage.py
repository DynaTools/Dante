"""
Tests for local storage utilities.
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
import json
import base64
from cryptography.fernet import Fernet, InvalidToken  # Import InvalidToken

# Import functions directly, no LocalStorage class exists
from utils.local_storage import save_key, get_key, clear_key, sync_session_state, _get_encryption_key

# Mock the streamlit object and its session_state
@pytest.fixture
def mock_streamlit():
    with patch('utils.local_storage.st') as mock_st:
        mock_st.session_state = {} # Use a simple dict to simulate session_state
        # Mock the session_id needed for encryption key generation
        mock_st.runtime.scriptrunner.script_run_context.get_script_run_ctx.return_value.session_id = "test_session_id"
        yield mock_st

# Mock Fernet for predictable encryption/decryption in tests
@pytest.fixture(autouse=True) # Apply this fixture automatically to all tests
def mock_fernet():
     # Keep the Fernet class mock for encrypt/decrypt
     with patch('utils.local_storage.Fernet') as mock_fernet_class:
        mock_fernet_instance = MagicMock()
        mock_fernet_instance.encrypt.side_effect = lambda data: data + b'_encrypted'
        # Modify decrypt side_effect to raise InvalidToken for bad data
        def decrypt_side_effect(data):
            if data.endswith(b'_encrypted'):
                return data[:-10]
            else:
                raise InvalidToken("Mock decryption failed")
        mock_fernet_instance.decrypt.side_effect = decrypt_side_effect
        mock_fernet_class.return_value = mock_fernet_instance
        yield mock_fernet_class # Only yield the class mock

# Patch _get_encryption_key directly for relevant tests
@patch('utils.local_storage._get_encryption_key', return_value=(b'test_key_32_bytes_long_12345678', b'test_salt_16_byt'))
def test_save_and_get_key(mock_get_enc_key, mock_streamlit):
    """Test saving and retrieving an API key using mocked session_state."""
    test_key = "test_api_key"
    test_value = "secret_value_123"
    storage_key = f"verborum_key_{test_key}"

    # Save key (will use mocked _get_encryption_key)
    save_key(test_key, test_value)

    # Verify session_state was updated with encrypted data and salt
    assert storage_key in mock_streamlit.session_state
    stored_data_json = mock_streamlit.session_state[storage_key]
    stored_data = json.loads(stored_data_json)
    assert 'value' in stored_data
    assert 'salt' in stored_data
    # Check if the stored value looks like our mocked encryption
    encrypted_value_bytes = base64.b64decode(stored_data['value'])
    assert encrypted_value_bytes == test_value.encode() + b'_encrypted'
    # Check if the salt matches the one returned by the mocked _get_encryption_key
    assert base64.b64decode(stored_data['salt']) == b'test_salt_16_byt'

    # Get key and verify (uses the mocked Fernet decryption and mocked _get_encryption_key)
    retrieved_value = get_key(test_key)
    assert retrieved_value == test_value
    # Ensure _get_encryption_key was called by get_key with the correct salt
    mock_get_enc_key.assert_called_with(b'test_salt_16_byt')


@patch('utils.local_storage._get_encryption_key', return_value=(b'test_key_32_bytes_long_12345678', b'test_salt_16_byt'))
def test_get_key_decryption_error(mock_get_enc_key, mock_streamlit):
    """Test error handling during key retrieval if decryption fails."""
    test_key = "decryption_error_key"
    storage_key = f"verborum_key_{test_key}"

    # Store some data that won't decrypt correctly with our mock
    bad_encrypted_data = base64.b64encode(b"this_wont_decrypt").decode('utf-8')
    salt_data = base64.b64encode(b'test_salt_16_byt').decode('utf-8')
    mock_streamlit.session_state[storage_key] = json.dumps({'value': bad_encrypted_data, 'salt': salt_data})

    # Mock st.error to check if it gets called
    with patch('utils.local_storage.st.error') as mock_st_error:
        retrieved_value = get_key(test_key)
        assert retrieved_value is None
        mock_st_error.assert_called_once()
        # Check that the error message contains something about the failure
        assert "Error retrieving key" in mock_st_error.call_args[0][0]


def test_get_key_not_found(mock_streamlit):
    """Test retrieving a key that doesn't exist."""
    assert get_key("non_existent_key") is None

def test_clear_key(mock_streamlit):
    """Test clearing an API key from session_state."""
    test_key = "test_api_key_to_clear"
    storage_key = f"verborum_key_{test_key}"

    # Add a dummy value to session_state first
    mock_streamlit.session_state[storage_key] = 'some_dummy_data'
    assert storage_key in mock_streamlit.session_state # Pre-check

    # Clear key
    clear_key(test_key)

    # Verify key was deleted from session_state
    assert storage_key not in mock_streamlit.session_state

def test_sync_session_state_initializes_keys(mock_streamlit):
    """Test that sync_session_state initializes keys if they don't exist."""
    # Ensure session_state is initially empty for this test
    mock_streamlit.session_state = {}

    sync_session_state()

    # Verify default keys are initialized to None
    assert 'deepl_key' in mock_streamlit.session_state and mock_streamlit.session_state['deepl_key'] is None
    assert 'gemini_key' in mock_streamlit.session_state and mock_streamlit.session_state['gemini_key'] is None
    assert 'openai_key' in mock_streamlit.session_state and mock_streamlit.session_state['openai_key'] is None

def test_sync_session_state_does_not_overwrite(mock_streamlit):
    """Test that sync_session_state doesn't overwrite existing keys."""
    mock_streamlit.session_state['deepl_key'] = "existing_deepl"
    mock_streamlit.session_state['gemini_key'] = "existing_gemini"
    # openai_key is missing

    sync_session_state()

    # Verify existing keys were not overwritten
    assert mock_streamlit.session_state['deepl_key'] == "existing_deepl"
    assert mock_streamlit.session_state['gemini_key'] == "existing_gemini"
    # Verify the missing key was initialized
    assert 'openai_key' in mock_streamlit.session_state and mock_streamlit.session_state['openai_key'] is None


def test_invalid_input():
    """Test handling of invalid input types for save_key."""
    with pytest.raises(ValueError):
        save_key(123, "value")  # Invalid key_name type

    with pytest.raises(ValueError):
        save_key("key", 123)  # Invalid value type