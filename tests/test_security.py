import pytest
from app.core.security import get_password_hash, verify_password, create_access_token
from jose import jwt
from app.core.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_unique(self):
        h1 = get_password_hash("samepassword")
        h2 = get_password_hash("samepassword")
        assert h1 != h2  # Different salts

    def test_hash_is_string(self):
        hashed = get_password_hash("test")
        assert isinstance(hashed, str)


class TestTokenCreation:
    def test_create_token_default_expiry(self):
        token = create_access_token(subject=42)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "42"
        assert "exp" in payload

    def test_create_token_custom_expiry(self):
        from datetime import timedelta
        token = create_access_token(subject=1, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "1"

    def test_token_is_string(self):
        token = create_access_token(subject="test")
        assert isinstance(token, str)
