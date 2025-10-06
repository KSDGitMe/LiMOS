"""
Authentication and Security for Receipt Processing API

This module provides authentication, authorization, and security utilities
for the receipt processing API endpoints.
"""

import hashlib
import hmac
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel


# Configuration (move to environment variables in production)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY_HEADER = "X-API-Key"

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    username: str
    email: str
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class APIKey(BaseModel):
    """API key model."""
    key_id: str
    key_hash: str
    user_id: str
    permissions: List[str]
    name: str
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    username: str
    permissions: List[str]
    exp: datetime


# In-memory storage (use database in production)
USERS_DB: Dict[str, User] = {
    "demo_user": User(
        user_id="demo_user",
        username="demo_user",
        email="demo@example.com",
        permissions=["read", "write", "admin"],
        created_at=datetime.utcnow()
    )
}

API_KEYS_DB: Dict[str, APIKey] = {
    "demo_key_hash": APIKey(
        key_id="demo_key",
        key_hash="demo_key_hash",
        user_id="demo_user",
        permissions=["read", "write"],
        name="Demo API Key",
        created_at=datetime.utcnow()
    )
}


class AuthManager:
    """Authentication and authorization manager."""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            permissions: List[str] = payload.get("permissions", [])
            exp: datetime = datetime.fromtimestamp(payload.get("exp"))

            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")

            return TokenData(user_id=user_id, username=username, permissions=permissions, exp=exp)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def verify_api_key(api_key: str) -> Optional[APIKey]:
        """Verify an API key and return associated data."""
        key_hash = AuthManager.hash_api_key(api_key)

        for stored_key in API_KEYS_DB.values():
            if stored_key.key_hash == key_hash and stored_key.is_active:
                # Check expiration
                if stored_key.expires_at and stored_key.expires_at < datetime.utcnow():
                    continue

                # Update last used
                stored_key.last_used = datetime.utcnow()
                return stored_key

        return None

    @staticmethod
    def get_user(user_id: str) -> Optional[User]:
        """Get user by ID."""
        return USERS_DB.get(user_id)

    @staticmethod
    def check_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        if "admin" in user_permissions:
            return True

        return all(perm in user_permissions for perm in required_permissions)


class RateLimiter:
    """Simple rate limiter for API endpoints."""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.limits = {
            "default": {"requests": 100, "window": 3600},  # 100 requests per hour
            "upload": {"requests": 20, "window": 3600},     # 20 uploads per hour
            "batch": {"requests": 5, "window": 3600}        # 5 batch jobs per hour
        }

    def is_allowed(self, identifier: str, endpoint_type: str = "default") -> bool:
        """Check if request is allowed based on rate limits."""
        now = datetime.utcnow()
        limit_config = self.limits.get(endpoint_type, self.limits["default"])

        # Clean old requests
        if identifier in self.requests:
            window_start = now - timedelta(seconds=limit_config["window"])
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []

        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit_config["requests"]:
            return False

        # Record this request
        self.requests[identifier].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Authentication dependencies
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Optional[User]:
    """Get current user from JWT token."""
    if not credentials:
        return None

    try:
        token_data = AuthManager.verify_token(credentials.credentials)
        user = AuthManager.get_user(token_data.user_id)

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive user")

        # Update last login
        user.last_login = datetime.utcnow()
        return user

    except HTTPException:
        raise
    except Exception:
        return None


async def get_current_user_from_api_key(
    api_key: Optional[str] = Depends(api_key_scheme)
) -> Optional[User]:
    """Get current user from API key."""
    if not api_key:
        return None

    key_data = AuthManager.verify_api_key(api_key)
    if not key_data:
        return None

    user = AuthManager.get_user(key_data.user_id)
    if not user or not user.is_active:
        return None

    return user


async def get_current_user(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key)
) -> Optional[User]:
    """Get current user from either token or API key."""
    return token_user or api_key_user


async def require_authentication(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication for endpoint access."""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


def require_permissions(required_permissions: List[str]):
    """Dependency factory for permission-based access control."""

    async def permission_dependency(
        current_user: User = Depends(require_authentication)
    ) -> User:
        if not AuthManager.check_permissions(current_user.permissions, required_permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        return current_user

    return permission_dependency


def rate_limit(endpoint_type: str = "default"):
    """Dependency factory for rate limiting."""

    async def rate_limit_dependency(
        request: Request,
        current_user: Optional[User] = Depends(get_current_user)
    ):
        # Use user ID if authenticated, otherwise use IP address
        identifier = current_user.user_id if current_user else request.client.host

        if not rate_limiter.is_allowed(identifier, endpoint_type):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

    return rate_limit_dependency


# Security utilities
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, f"sha256={expected_signature}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')


def validate_file_type(content_type: str, allowed_types: List[str]) -> bool:
    """Validate file content type."""
    return content_type in allowed_types


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename with timestamp and random component."""
    import os
    from pathlib import Path

    # Get file extension
    ext = Path(original_filename).suffix

    # Generate secure name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_part = secrets.token_hex(8)

    return f"{timestamp}_{random_part}{ext}"


# Authentication endpoints (for API key management)
class AuthEndpoints:
    """Authentication-related endpoints."""

    @staticmethod
    async def login(username: str, password: str) -> Dict[str, Any]:
        """Login endpoint (simplified for demo)."""
        # In production, verify password hash
        user = USERS_DB.get(username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthManager.create_access_token(
            data={
                "sub": user.user_id,
                "username": user.username,
                "permissions": user.permissions
            },
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "permissions": user.permissions
            }
        }

    @staticmethod
    async def create_api_key(
        user: User,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new API key for the user."""
        # Validate permissions
        if not AuthManager.check_permissions(user.permissions, permissions):
            raise HTTPException(
                status_code=403,
                detail="Cannot create API key with permissions you don't have"
            )

        # Generate new API key
        api_key = AuthManager.generate_api_key()
        key_hash = AuthManager.hash_api_key(api_key)
        key_id = secrets.token_hex(8)

        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        api_key_record = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user.user_id,
            permissions=permissions,
            name=name,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

        # Store in database
        API_KEYS_DB[key_hash] = api_key_record

        return {
            "api_key": api_key,  # Only returned once!
            "key_id": key_id,
            "name": name,
            "permissions": permissions,
            "expires_at": expires_at,
            "created_at": api_key_record.created_at
        }

    @staticmethod
    async def list_api_keys(user: User) -> List[Dict[str, Any]]:
        """List user's API keys (without revealing the actual keys)."""
        user_keys = [
            key for key in API_KEYS_DB.values()
            if key.user_id == user.user_id
        ]

        return [
            {
                "key_id": key.key_id,
                "name": key.name,
                "permissions": key.permissions,
                "is_active": key.is_active,
                "created_at": key.created_at,
                "last_used": key.last_used,
                "expires_at": key.expires_at
            }
            for key in user_keys
        ]

    @staticmethod
    async def revoke_api_key(user: User, key_id: str) -> Dict[str, str]:
        """Revoke an API key."""
        for key in API_KEYS_DB.values():
            if key.key_id == key_id and key.user_id == user.user_id:
                key.is_active = False
                return {"message": "API key revoked successfully"}

        raise HTTPException(status_code=404, detail="API key not found")