"""
Browser local storage interface for managing API keys and user preferences.
Uses Streamlit session state with browser-local persistence.
"""

import base64
import json
import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def _get_encryption_key(salt: bytes = None) -> tuple[bytes, bytes]:
    """Generate encryption key using a salt and device-specific info."""
    if salt is None:
        salt = Fernet.generate_key()[:16]  # Use first 16 bytes as salt
    
    # Use session info as base for key derivation
    base_key = st.runtime.scriptrunner.script_run_context.get_script_run_ctx().session_id.encode()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(base_key))
    return key, salt

def save_key(key_name: str, value: str) -> None:
    """Save an API key to session state with basic encryption."""
    if not isinstance(key_name, str) or not isinstance(value, str):
        raise ValueError("key_name and value must be strings")
    
    # Generate encryption key and encrypt value
    key, salt = _get_encryption_key()
    f = Fernet(key)
    encrypted_value = f.encrypt(value.encode())
    
    # Store encrypted value and salt
    storage_data = {
        'value': base64.b64encode(encrypted_value).decode('utf-8'),
        'salt': base64.b64encode(salt).decode('utf-8')
    }
    st.session_state[f"dante_ai_key_{key_name}"] = json.dumps(storage_data)

def get_key(key_name: str) -> str:
    """Retrieve and decrypt an API key from session state."""
    storage_key = f"dante_ai_key_{key_name}"
    stored_data = st.session_state.get(storage_key)
    
    if not stored_data:
        return None
        
    try:
        data = json.loads(stored_data)
        encrypted_value = base64.b64decode(data['value'])
        salt = base64.b64decode(data['salt'])
        
        # Regenerate key with stored salt
        key, _ = _get_encryption_key(salt)
        f = Fernet(key)
        
        # Decrypt value
        decrypted_value = f.decrypt(encrypted_value)
        return decrypted_value.decode('utf-8')
    except Exception as e:
        st.error(f"Error retrieving key: {str(e)}")
        return None

def clear_key(key_name: str) -> None:
    """Remove an API key from session state."""
    storage_key = f"dante_ai_key_{key_name}"
    if storage_key in st.session_state:
        del st.session_state[storage_key]

def sync_session_state() -> None:
    """Initialize session state with default values if not present."""
    # Initialize API key slots if not present
    for key in ['deepl_key', 'gemini_key', 'openai_key']:
        if key not in st.session_state:
            st.session_state[key] = None