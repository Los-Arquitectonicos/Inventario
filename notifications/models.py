"""
Pydantic models for the Notifications microservice.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# ============ ROLES ============
class UserRole(str, Enum):
    """Available user roles in the system."""
    ADMIN = "admin"
    OPERARIO_BODEGA = "operario_bodega"
    EMPACADOR = "empacador"
    OPERARIO_CONTROL_CALIDAD = "operario_control_calidad"


# ============ NOTIFICATIONS ============
class NotificationBase(BaseModel):
    """Base notification model."""
    message: str = Field(..., min_length=1, max_length=1000)


class NotificationCreate(NotificationBase):
    """Model for creating a notification."""
    recipient_username: Optional[str] = None  # Send to specific user
    recipient_roles: Optional[List[UserRole]] = None  # Send to users with these roles


class NotificationInDB(NotificationBase):
    """Notification as stored in MongoDB (embedded in user document)."""
    id: str = Field(..., alias="_id")
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False
    sender_username: str


class NotificationResponse(BaseModel):
    """Notification response model."""
    id: str
    message: str
    sent_at: datetime
    read: bool
    sender_username: str

    class Config:
        from_attributes = True


# ============ USERS ============
class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = "p.sanin@uniandes.edu.co"  # Default email for testing
    role: UserRole = UserRole.OPERARIO_BODEGA


class UserCreate(UserBase):
    """Model for creating a user."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Model for updating a user."""
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=6)


class UserInDB(UserBase):
    """User as stored in MongoDB."""
    id: str = Field(..., alias="_id")
    hashed_password: str
    notifications: List[NotificationInDB] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    notification_count: int = 0

    class Config:
        from_attributes = True


class UserWithNotifications(UserResponse):
    """User with their notifications."""
    notifications: List[NotificationResponse] = []


# ============ AUTH ============
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
