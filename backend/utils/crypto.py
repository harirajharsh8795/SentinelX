import os
from cryptography.fernet import Fernet

# Phase 12: At-rest encryption mock/logic
# In production, securely load this from Azure Key Vault or AWS KMS
key_str = os.environ.get("FILE_ENCRYPTION_KEY")
if not key_str:
    # Use a stable key for development to avoid data loss on restarts
    key_str = "dBjX7Xg_zL3T5fVp6lK9w2v8t5k3M2c8x7Y6j8H1G2A="
ENCRYPTION_KEY = key_str.encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_file_data(data: bytes) -> bytes:
    """
    Encrypts file data at-rest using AES-128 via Fernet.
    """
    return cipher_suite.encrypt(data)

def decrypt_file_data(encrypted_data: bytes) -> bytes:
    """
    Decrypts at-rest file data.
    """
    return cipher_suite.decrypt(encrypted_data)
