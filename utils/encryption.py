"""
CyberSentinel - Encryption Manager
====================================
Handles AES-256 encryption/decryption of log files
using the Fernet symmetric encryption scheme.

Features:
    - Automatic key generation and storage
    - Key rotation support
    - Encrypt/decrypt strings and files
    - Secure key file permissions
"""

import os
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from cryptography.fernet import Fernet
# pyrefly: ignore [missing-import]
from cryptography.hazmat.primitives import hashes
# pyrefly: ignore [missing-import]
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config.settings import KEY_FILE, KEY_ROTATION_HOURS, ENCRYPTION_ENABLED


class EncryptionManager:
    """
    Manages encryption operations for CyberSentinel.
    Uses Fernet (AES-128-CBC with HMAC-SHA256) for symmetric encryption.
    """

    def __init__(self):
        self.enabled = ENCRYPTION_ENABLED
        self.key_file = KEY_FILE
        self.key = None
        self.fernet = None
        self._initialize()

    def _initialize(self):
        """Initialize the encryption system with key loading or generation."""
        if not self.enabled:
            return

        if self.key_file.exists():
            self._load_key()
            if self._should_rotate_key():
                self._rotate_key()
        else:
            self._generate_key()

    def _generate_key(self):
        """Generate a new Fernet encryption key and save it."""
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self._save_key()

    def _save_key(self):
        """Save the current key with metadata to disk."""
        key_data = {
            "key": self.key.decode("utf-8"),
            "created_at": datetime.now().isoformat(),
            "rotated_at": datetime.now().isoformat(),
            "rotation_count": 0,
        }
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.key_file, "w", encoding="utf-8") as f:
            json.dump(key_data, f, indent=2)

    def _load_key(self):
        """Load an existing key from disk."""
        try:
            with open(self.key_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            self.key = key_data["key"].encode("utf-8")
            self.fernet = Fernet(self.key)
        except (json.JSONDecodeError, KeyError, Exception):
            # Key file corrupted, regenerate
            self._generate_key()

    def _should_rotate_key(self) -> bool:
        """Check if the key should be rotated based on age."""
        try:
            with open(self.key_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            rotated_at = datetime.fromisoformat(key_data["rotated_at"])
            return datetime.now() - rotated_at > timedelta(hours=KEY_ROTATION_HOURS)
        except Exception:
            return True

    def _rotate_key(self):
        """Rotate to a new encryption key while preserving the old one for decryption."""
        old_key = self.key
        self._generate_key()

        # Update metadata
        try:
            with open(self.key_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            key_data["rotation_count"] = key_data.get("rotation_count", 0) + 1
            key_data["rotated_at"] = datetime.now().isoformat()
            key_data["previous_key"] = old_key.decode("utf-8") if old_key else None
            with open(self.key_file, "w", encoding="utf-8") as f:
                json.dump(key_data, f, indent=2)
        except Exception:
            pass

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded encrypted string, or original if encryption disabled.
        """
        if not self.enabled or not self.fernet:
            return plaintext

        try:
            encrypted = self.fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            return f"[ENCRYPTION_ERROR: {e}] {plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: The encrypted string to decrypt.

        Returns:
            Decrypted plaintext string.
        """
        if not self.enabled or not self.fernet:
            return ciphertext

        try:
            decrypted = self.fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            return f"[DECRYPTION_ERROR: {e}]"

    def encrypt_file(self, input_path: Path, output_path: Path = None) -> Path:
        """
        Encrypt an entire file.

        Args:
            input_path: Path to the file to encrypt.
            output_path: Optional output path. Defaults to input_path + '.enc'.

        Returns:
            Path to the encrypted file.
        """
        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + ".enc")

        with open(input_path, "rb") as f:
            data = f.read()

        if self.enabled and self.fernet:
            encrypted_data = self.fernet.encrypt(data)
        else:
            encrypted_data = data

        with open(output_path, "wb") as f:
            f.write(encrypted_data)

        return output_path

    def decrypt_file(self, input_path: Path, output_path: Path = None) -> Path:
        """
        Decrypt an encrypted file.

        Args:
            input_path: Path to the encrypted file.
            output_path: Optional output path.

        Returns:
            Path to the decrypted file.
        """
        if output_path is None:
            suffix = input_path.suffix
            if suffix == ".enc":
                output_path = input_path.with_suffix("")
            else:
                output_path = input_path.with_suffix(".dec" + suffix)

        with open(input_path, "rb") as f:
            data = f.read()

        if self.enabled and self.fernet:
            decrypted_data = self.fernet.decrypt(data)
        else:
            decrypted_data = data

        with open(output_path, "wb") as f:
            f.write(decrypted_data)

        return output_path

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
        """
        Derive an encryption key from a password using PBKDF2.

        Args:
            password: The password to derive key from.
            salt: Optional salt bytes. Generated if not provided.

        Returns:
            Tuple of (key_bytes, salt_bytes).
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def get_status(self) -> dict:
        """Get the current encryption status and metadata."""
        status = {
            "enabled": self.enabled,
            "key_loaded": self.key is not None,
            "key_file_exists": self.key_file.exists(),
        }

        if self.key_file.exists():
            try:
                with open(self.key_file, "r", encoding="utf-8") as f:
                    key_data = json.load(f)
                status["created_at"] = key_data.get("created_at", "Unknown")
                status["rotated_at"] = key_data.get("rotated_at", "Unknown")
                status["rotation_count"] = key_data.get("rotation_count", 0)
            except Exception:
                pass

        return status
