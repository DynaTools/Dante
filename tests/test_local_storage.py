"""
Tests for local storage utilities.
"""

import pytest
from unittest.mock import MagicMock, patch
from utils.local_storage import save_key, get_key, clear_key, sync_session_state

@pytest.fixture
def mock_storage():
    with patch('utils.local_storage.LocalStorage') as mock:
        storage_instance = MagicMock()
        mock.return_value = storage_instance
        yield storage_instance

@pytest.fixture
def mock_streamlit():
    with patch('utils.local_storage.st') as mock_st:
        # Mock browser info for key derivation
        mock_st.runtime.get_instance.return_value.browser_info.browser = "Chrome"
        mock_st.runtime.get_instance.return_value.browser_info.user_agent = "test_agent"
        yield mock_st

def test_save_and_get_key(mock_storage, mock_streamlit):
    """Test saving and retrieving an API key."""
    test_key = "test_api_key"
    test_value = "secret_value_123"
    
    # Save key
    save_key(test_key, test_value)
    
    # Verify storage was called with encrypted data
    assert mock_storage.__setitem__.called
    stored_key = mock_storage.__setitem__.call_args[0][0]
    assert stored_key == f"verborum_key_{test_key}"
    
    # Mock storage retrieval
    mock_storage.get.return_value = mock_storage.__setitem__.call_args[0][1]
    
    # Get key and verify
    retrieved_value = get_key(test_key)
    assert retrieved_value == test_value

def test_clear_key(mock_storage):
    """Test clearing an API key."""
    test_key = "test_api_key"
    storage_key = f"verborum_key_{test_key}"
    
    # Mock key existence
    mock_storage.__contains__.return_value = True
    
    # Clear key
    clear_key(test_key)
    
    # Verify key was deleted
    assert mock_storage.__delitem__.called
    assert mock_storage.__delitem__.call_args[0][0] == storage_key

def test_sync_session_state(mock_storage, mock_streamlit):
    """Test syncing keys to session state."""
    # Mock stored keys
    stored_keys = {
        "deepl_key": "test_deepl",
        "gemini_key": "test_gemini",
        "openai_key": "test_openai"
    }
    
    def mock_get(key):
        base_key = key.replace("verborum_key_", "")
        if base_key in stored_keys:
            # Create mock encrypted data
            return '{"value": "encrypted", "salt": "salt"}'
        return None
    
    mock_storage.get.side_effect = mock_get
    
    # Mock successful decryption
    with patch('utils.local_storage.Fernet') as mock_fernet:
        mock_fernet_instance = MagicMock()
        mock_fernet.return_value = mock_fernet_instance
        mock_fernet_instance.decrypt.side_effect = lambda x: stored_keys[x.decode()].encode()
        
        # Run sync
        sync_session_state()
        
        # Verify session state was updated
        for key, value in stored_keys.items():
            assert mock_streamlit.session_state[key] == value

def test_invalid_input():
    """Test handling of invalid input."""
    with pytest.raises(ValueError):
        save_key(123, "value")  # Invalid key_name type
    
    with pytest.raises(ValueError):
        save_key("key", 123)  # Invalid value type