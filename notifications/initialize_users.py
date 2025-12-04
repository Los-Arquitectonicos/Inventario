"""
Initialize default users if database is empty.
"""
from datetime import datetime
from auth import get_password_hash
from models import UserRole


# Default users to create if database is empty
DEFAULT_USERS = [
    {
        "username": "admin",
        "email": "p.sanin@uniandes.edu.co",
        "role": UserRole.ADMIN.value,
        "password": "admin123"
    },
    {
        "username": "operario1",
        "email": "p.sanin@uniandes.edu.co",
        "role": UserRole.OPERARIO_BODEGA.value,
        "password": "operario123"
    },
    {
        "username": "empacador1",
        "email": "p.sanin@uniandes.edu.co",
        "role": UserRole.EMPACADOR.value,
        "password": "empacador123"
    },
    {
        "username": "calidad1",
        "email": "p.sanin@uniandes.edu.co",
        "role": UserRole.OPERARIO_CONTROL_CALIDAD.value,
        "password": "calidad123"
    }
]


async def initialize_users(users_collection) -> bool:
    """
    Initialize default users if the database is empty.
    
    Args:
        users_collection: MongoDB users collection
    
    Returns:
        True if users were created, False if database already had users
    """
    # Check if collection is empty
    count = await users_collection.count_documents({})
    
    if count > 0:
        print(f"ℹ️  Database already has {count} users. Skipping initialization.")
        return False
    
    print("📝 Database is empty. Creating default users...")
    
    # Create users
    for user_data in DEFAULT_USERS:
        user_doc = {
            "_id": user_data["username"],  # Use username as _id for simplicity
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"],
            "hashed_password": get_password_hash(user_data["password"]),
            "notifications": [],
            "created_at": datetime.utcnow()
        }
        
        await users_collection.insert_one(user_doc)
        print(f"  ✅ Created user: {user_data['username']} (role: {user_data['role']})")
    
    print(f"✅ Successfully created {len(DEFAULT_USERS)} default users")
    return True
