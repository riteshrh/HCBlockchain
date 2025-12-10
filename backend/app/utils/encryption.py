
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings
import os

class EncryptionService:
    def __init__(self, key: str = None):
        if key is None:
            if not settings.encryption_key:
                raise ValueError("ENCRYPTION_KEY must be set in environment variables")
            key = settings.encryption_key.encode()
        else:
            key = key.encode() if isinstance(key, str) else key
        
        # Ensure key is 32 bytes for AES-256
        # If key is not exactly 32 bytes, derive it using PBKDF2 with a fixed salt
        if len(key) != 32:
            # Use a fixed salt based on the key itself to ensure consistency
            import hashlib
            salt = hashlib.sha256(key).digest()[:16]  # Use first 16 bytes of key hash as salt
            key = self._derive_key(key, salt)
        
        self.key = key
    
    @staticmethod
    def _generate_key() -> bytes:
        return os.urandom(32)
    
    @staticmethod
    def _derive_key(password: bytes, salt: bytes = None) -> bytes:
        if salt is None:
            # Use a fixed salt based on password hash for consistency
            import hashlib
            salt = hashlib.sha256(password).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password)
    
    def encrypt(self, plaintext: str) -> str:
        # Convert string to bytes
        plaintext_bytes = plaintext.encode('utf-8')
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext_bytes) + padder.finalize()
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Prepend IV to ciphertext
        encrypted_data = iv + ciphertext
        
        # Return base64-encoded result
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            raise ValueError("Ciphertext cannot be empty")
        
        try:
            # Decode base64
            encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {str(e)}")
        
        # Check minimum length (IV + at least 16 bytes of ciphertext)
        if len(encrypted_data) < 32:
            raise ValueError(f"Encrypted data too short: expected at least 32 bytes, got {len(encrypted_data)}")
        
        # Extract IV (first 16 bytes)
        iv = encrypted_data[:16]
        ciphertext_bytes = encrypted_data[16:]
        
        if len(ciphertext_bytes) < 16:
            raise ValueError(f"Ciphertext too short: expected at least 16 bytes, got {len(ciphertext_bytes)}")
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        try:
            padded_plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
        
        # Unpad
        try:
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        except ValueError as e:
            # Invalid padding bytes
            raise ValueError(f"Invalid padding bytes: {str(e)}. This may indicate data corruption or encryption key mismatch.")
        except Exception as e:
            raise ValueError(f"Unpadding failed: {str(e)}")
        
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode decrypted data as UTF-8: {str(e)}")

# Global encryption service instance
try:
    encryption_service = EncryptionService()
    # Verify encryption key is set
    if not settings.encryption_key:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("ENCRYPTION_KEY is not set! Encryption/decryption may fail.")
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Encryption service initialized with key length: {len(settings.encryption_key)}")
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize encryption service: {e}")
    raise
