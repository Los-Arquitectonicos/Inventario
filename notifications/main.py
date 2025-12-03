"""
Notifications Microservice - FastAPI Application

A simple microservice for managing users, authentication, and notifications.
Sends email notifications via Amazon SES.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from database import Database, get_users_collection
from models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithNotifications,
    NotificationCreate,
    NotificationResponse,
    LoginRequest,
    Token,
    TokenData,
    UserRole,
)
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin,
)
from email_service import send_notification_email
from initialize_users import initialize_users


# ============ APP LIFECYCLE ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    await Database.connect()

    # Initialize default users if database is empty
    users_collection = get_users_collection()
    await initialize_users(users_collection)

    yield

    # Shutdown
    await Database.disconnect()


# ============ APP CONFIGURATION ============
app = FastAPI(
    title="Notifications Microservice",
    description="API for managing users and notifications with email support via Amazon SES",
    version="1.0.0",
    lifespan=lifespan,
    # root_path="/notifications",  # Comentado para acceso directo, Kong usa strip_path=true
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ HEALTH CHECK ============
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notifications",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============ AUTHENTICATION ============
@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT token.
    Token expires in 24 hours.
    """
    users = get_users_collection()

    # Find user
    user = await users.find_one({"username": login_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create token
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return Token(access_token=access_token)


# ============ USERS ============
@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
async def create_user(user: UserCreate, admin: TokenData = Depends(require_admin)):
    """
    Create a new user. Requires admin role.
    """
    users = get_users_collection()

    # Check if username exists
    existing = await users.find_one({"username": user.username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    # Create user document
    user_doc = {
        "_id": user.username,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "hashed_password": get_password_hash(user.password),
        "notifications": [],
        "created_at": datetime.utcnow(),
    }

    await users.insert_one(user_doc)

    return UserResponse(
        id=user_doc["_id"],
        username=user_doc["username"],
        email=user_doc["email"],
        role=UserRole(user_doc["role"]),
        created_at=user_doc["created_at"],
        notification_count=0,
    )


@app.get("/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    List all users. Optionally filter by role.
    """
    users = get_users_collection()

    query = {}
    if role:
        query["role"] = role.value

    cursor = users.find(query)
    result = []

    async for user in cursor:
        result.append(
            UserResponse(
                id=user["_id"],
                username=user["username"],
                email=user["email"],
                role=UserRole(user["role"]),
                created_at=user["created_at"],
                notification_count=len(user.get("notifications", [])),
            )
        )

    return result


@app.get("/users/me", response_model=UserWithNotifications, tags=["Users"])
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Get current user info with their notifications.
    """
    users = get_users_collection()

    user = await users.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = [
        NotificationResponse(
            id=n["_id"],
            message=n["message"],
            sent_at=n["sent_at"],
            read=n["read"],
            sender_username=n["sender_username"],
        )
        for n in user.get("notifications", [])
    ]

    return UserWithNotifications(
        id=user["_id"],
        username=user["username"],
        email=user["email"],
        role=UserRole(user["role"]),
        created_at=user["created_at"],
        notification_count=len(notifications),
        notifications=notifications,
    )


@app.get("/users/{username}", response_model=UserResponse, tags=["Users"])
async def get_user(username: str, current_user: TokenData = Depends(get_current_user)):
    """
    Get a specific user by username.
    """
    users = get_users_collection()

    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["_id"],
        username=user["username"],
        email=user["email"],
        role=UserRole(user["role"]),
        created_at=user["created_at"],
        notification_count=len(user.get("notifications", [])),
    )


@app.put("/users/{username}", response_model=UserResponse, tags=["Users"])
async def update_user(
    username: str, user_update: UserUpdate, admin: TokenData = Depends(require_admin)
):
    """
    Update a user. Requires admin role.
    """
    users = get_users_collection()

    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.role is not None:
        update_data["role"] = user_update.role.value
    if user_update.password is not None:
        update_data["hashed_password"] = get_password_hash(user_update.password)

    if update_data:
        await users.update_one({"username": username}, {"$set": update_data})
        user = await users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return UserResponse(
        id=user["_id"],
        username=user["username"],
        email=user["email"],
        role=UserRole(user["role"]),
        created_at=user["created_at"],
        notification_count=len(user.get("notifications", [])),
    )


@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(username: str, admin: TokenData = Depends(require_admin)):
    """
    Delete a user. Requires admin role.
    """
    users = get_users_collection()

    result = await users.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")


# ============ NOTIFICATIONS ============
@app.post("/send", response_model=dict, tags=["Notifications"])
async def send_notification(
    notification: NotificationCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Send a notification to a user or users by role.

    - `recipient_username`: Send to a specific user
    - `recipient_roles`: Send to all users with these roles

    At least one of the above must be specified.
    """
    users = get_users_collection()

    if not notification.recipient_username and not notification.recipient_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either recipient_username or recipient_roles",
        )

    # Build query for recipients
    query = {}
    if notification.recipient_username:
        query["username"] = notification.recipient_username
    elif notification.recipient_roles:
        query["role"] = {"$in": [r.value for r in notification.recipient_roles]}

    # Find recipients
    recipients = await users.find(query).to_list(length=1000)

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No recipients found"
        )

    # Create notification document
    notification_id = str(uuid.uuid4())
    notification_doc = {
        "_id": notification_id,
        "message": notification.message,
        "sent_at": datetime.utcnow(),
        "read": False,
        "sender_username": current_user.username,
    }

    # Add notification to each recipient and send email
    sent_count = 0
    email_sent = 0

    for recipient in recipients:
        # Add to notifications array in MongoDB
        await users.update_one(
            {"username": recipient["username"]},
            {"$push": {"notifications": notification_doc}},
        )
        sent_count += 1

        # Send email notification
        email_success = await send_notification_email(
            recipient_email=recipient["email"],
            subject="Nueva Notificación",
            message=notification.message,
            sender_username=current_user.username or "system",
        )
        if email_success:
            email_sent += 1

    return {
        "success": True,
        "notification_id": notification_id,
        "recipients_count": sent_count,
        "emails_sent": email_sent,
        "message": f"Notification sent to {sent_count} user(s)",
    }


@app.get("/inbox", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_inbox(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get current user's notifications (inbox).
    """
    users = get_users_collection()

    user = await users.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = user.get("notifications", [])

    if unread_only:
        notifications = [n for n in notifications if not n["read"]]

    # Sort by sent_at descending (newest first)
    notifications.sort(key=lambda x: x["sent_at"], reverse=True)

    return [
        NotificationResponse(
            id=n["_id"],
            message=n["message"],
            sent_at=n["sent_at"],
            read=n["read"],
            sender_username=n["sender_username"],
        )
        for n in notifications
    ]


@app.put(
    "/inbox/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
async def mark_as_read(
    notification_id: str, current_user: TokenData = Depends(get_current_user)
):
    """
    Mark a notification as read.
    """
    users = get_users_collection()

    # Update the specific notification in the array
    result = await users.update_one(
        {"username": current_user.username, "notifications._id": notification_id},
        {"$set": {"notifications.$.read": True}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Get updated notification
    user = await users.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notification = next(
        (n for n in user.get("notifications", []) if n["_id"] == notification_id), None
    )

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse(
        id=notification["_id"],
        message=notification["message"],
        sent_at=notification["sent_at"],
        read=notification["read"],
        sender_username=notification["sender_username"],
    )


@app.put("/inbox/read-all", response_model=dict, tags=["Notifications"])
async def mark_all_as_read(current_user: TokenData = Depends(get_current_user)):
    """
    Mark all notifications as read.
    """
    users = get_users_collection()

    await users.update_one(
        {"username": current_user.username}, {"$set": {"notifications.$[].read": True}}
    )

    return {"success": True, "message": "All notifications marked as read"}


# ============ ROLES ============
@app.get("/roles", response_model=List[str], tags=["Roles"])
async def list_roles():
    """
    List all available roles.
    """
    return [role.value for role in UserRole]


# ============ MAIN ============
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
