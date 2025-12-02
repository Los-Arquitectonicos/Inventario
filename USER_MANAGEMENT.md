# User Management Guide

## Overview

This guide covers user creation, management, and email configuration for the ProvesiWMS system. Users created in the main Django application can authenticate and receive notifications through the notifications microservice.

## Pre-configured Users

The system comes with three default users:

| Username | Email | Password | Role | Description |
|----------|-------|----------|------|-------------|
| `admin` | admin@provesi.com | ProvesiAdmin2024! | Administrator | Full system access |
| `gerente` | gerente@provesi.com | Gerente2024! | Manager | Department management |
| `empleado` | empleado@provesi.com | Empleado2024! | Employee | Basic operations |

## Method 1: Using Django Admin Interface

### Access Django Admin

1. Navigate to: `https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/admin/`
2. Login with admin credentials:
   - Username: `admin`
   - Password: `ProvesiAdmin2024!`

### Create New User

1. Click **"Users"** in the Authentication section
2. Click **"Add User"**
3. Fill required fields:
   - Username: `nuevo_usuario`
   - Password: `SecurePassword123!`
   - Confirm password
4. Click **"Save and continue editing"**
5. Add additional information:
   - First name: `Juan`
   - Last name: `Pérez`
   - Email: `juan.perez@provesi.com`
   - Active: ✓ (checked)
   - Staff status: ✓ (if admin access needed)

### Create Inventory User Profile

After creating the Django user:

1. Go to **"Inventario"** → **"Usuarios"**
2. Click **"Add Usuario"**
3. Fill fields:
   - Nombre usuario: `nuevo_usuario` (same as Django username)
   - Email: `juan.perez@provesi.com`
   - Teléfono: `+57 300 123 4567`
   - Rol: Select from dropdown (`admin`, `gerente`, `empleado`)

## Method 2: Using setup_users.py Script

### Basic Usage

1. SSH to the application server:
```bash
ssh ubuntu@98.92.123.247  # Use IP from addresses file
```

2. Navigate to application directory:
```bash
cd /home/ubuntu/Inventario/ProvesiWMS
```

3. Run the setup script:
```bash
python setup_users.py
```

### Custom User Creation

Modify the script to add new users:

```python
#!/usr/bin/env python
"""
Extended user creation script for ProvesiWMS
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')
django.setup()

from django.contrib.auth.models import User
from inventario.models import Usuario

def create_custom_user(username, email, password, first_name, last_name, phone, role):
    """Create a new user with inventory profile."""
    
    print(f"Creating user: {username}")
    
    # Create Django User
    if not User.objects.filter(username=username).exists():
        django_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        print(f"✅ Django user created: {django_user.username}")
    else:
        django_user = User.objects.get(username=username)
        print(f"ℹ️ Django user already exists: {django_user.username}")
    
    # Create Inventory User
    if not Usuario.objects.filter(nombre_usuario=username).exists():
        inventory_user = Usuario.objects.create(
            nombre_usuario=username,
            email=email,
            telefono=phone,
            rol=role
        )
        print(f"✅ Inventory user created: {inventory_user.nombre_usuario}")
        print(f"   Role: {inventory_user.rol}")
        print(f"   Email: {inventory_user.email}")
        print(f"   Phone: {inventory_user.telefono}")
    else:
        print("ℹ️ Inventory user already exists")
    
    return django_user

def create_multiple_users():
    """Create multiple users for different departments."""
    
    users_to_create = [
        {
            'username': 'supervisor_almacen',
            'email': 'supervisor.almacen@provesi.com',
            'password': 'SuperAlmacen2024!',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'phone': '+57 300 111 2233',
            'role': 'gerente'
        },
        {
            'username': 'operario_1',
            'email': 'operario1@provesi.com',
            'password': 'Operario2024!',
            'first_name': 'María',
            'last_name': 'González',
            'phone': '+57 301 222 3344',
            'role': 'empleado'
        },
        {
            'username': 'operario_2',
            'email': 'operario2@provesi.com',
            'password': 'Operario2024!',
            'first_name': 'Pedro',
            'last_name': 'Martínez',
            'phone': '+57 302 333 4455',
            'role': 'empleado'
        },
        {
            'username': 'contador',
            'email': 'contador@provesi.com',
            'password': 'Contador2024!',
            'first_name': 'Ana',
            'last_name': 'López',
            'phone': '+57 303 444 5566',
            'role': 'gerente'
        }
    ]
    
    print("Creating multiple users for ProvesiWMS")
    print("=" * 50)
    
    for user_data in users_to_create:
        create_custom_user(**user_data)
        print("-" * 30)
    
    print("✅ All users created successfully!")

if __name__ == '__main__':
    # Create multiple users
    create_multiple_users()
    
    # Or create individual user
    # create_custom_user(
    #     username='mi_usuario',
    #     email='mi.usuario@provesi.com',
    #     password='MiPassword2024!',
    #     first_name='Nombre',
    #     last_name='Apellido',
    #     phone='+57 300 000 0000',
    #     role='empleado'
    # )
```

Save this as `create_users_extended.py` and run:

```bash
python create_users_extended.py
```

## Method 3: Using Django Management Commands

### Create Superuser

```bash
python manage.py createsuperuser --username=nuevo_admin --email=admin2@provesi.com
```

### Create Regular User via Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from inventario.models import Usuario

# Create Django User
user = User.objects.create_user(
    username='test_user',
    email='test@provesi.com',
    password='TestUser2024!',
    first_name='Test',
    last_name='User'
)

# Create Inventory Profile
inventory_user = Usuario.objects.create(
    nombre_usuario='test_user',
    email='test@provesi.com',
    telefono='+57 300 999 8877',
    rol='empleado'
)

print(f"User created: {user.username}")
print(f"Inventory profile: {inventory_user.rol}")
```

## User Roles and Permissions

### Role Definitions

| Role | Code | Permissions | Notification Access |
|------|------|-------------|-------------------|
| Administrator | `admin` | Full system access, user management, system configuration | All notifications, system alerts |
| Manager | `gerente` | Department management, inventory oversight, reports | Department notifications, alerts |
| Employee | `empleado` | Basic inventory operations, order processing | Personal notifications, task alerts |

### Role-based Notification Examples

```python
# In your notification creation logic:

def send_role_based_notification(message, role=None, specific_user=None):
    """Send notifications based on user role."""
    
    if specific_user:
        # Send to specific user
        create_notification(
            type="info",
            title="Personal Message",
            message=message,
            targetUser=specific_user
        )
    elif role == "admin":
        # Send to all admins
        admin_users = Usuario.objects.filter(rol='admin')
        for admin in admin_users:
            create_notification(
                type="warning",
                title="System Alert",
                message=message,
                targetUser=admin.email
            )
    elif role == "gerente":
        # Send to all managers
        managers = Usuario.objects.filter(rol='gerente')
        for manager in managers:
            create_notification(
                type="info",
                title="Management Update",
                message=message,
                targetUser=manager.email
            )
```

## Email Configuration

### Setting Up Email for Users

#### 1. Email Validation

Ensure all users have valid email addresses:

```python
def validate_email_format(email):
    """Validate email format."""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def update_user_email(username, new_email):
    """Update user email in both Django and Inventory models."""
    
    if not validate_email_format(new_email):
        raise ValueError("Invalid email format")
    
    # Update Django user
    django_user = User.objects.get(username=username)
    django_user.email = new_email
    django_user.save()
    
    # Update Inventory user
    inventory_user = Usuario.objects.get(nombre_usuario=username)
    inventory_user.email = new_email
    inventory_user.save()
    
    print(f"Email updated for {username}: {new_email}")
```

#### 2. Email Domain Configuration

For corporate environments, ensure proper email domains:

```python
ALLOWED_EMAIL_DOMAINS = [
    'provesi.com',
    'empresa.com',
    'gmail.com',  # For testing
]

def validate_corporate_email(email):
    """Validate email against allowed domains."""
    
    domain = email.split('@')[1].lower()
    return domain in ALLOWED_EMAIL_DOMAINS
```

#### 3. Bulk Email Operations

```python
def bulk_update_emails():
    """Update multiple user emails."""
    
    email_updates = {
        'supervisor_almacen': 'carlos.supervisor@provesi.com',
        'operario_1': 'maria.operario@provesi.com',
        'operario_2': 'pedro.operario@provesi.com',
        'contador': 'ana.contador@provesi.com'
    }
    
    for username, new_email in email_updates.items():
        try:
            update_user_email(username, new_email)
        except Exception as e:
            print(f"Error updating {username}: {e}")
```

## Testing User Authentication

### Test Login for New Users

```bash
#!/bin/bash
# Test authentication for all users

users=(
    "admin:ProvesiAdmin2024!"
    "gerente:Gerente2024!"
    "empleado:Empleado2024!"
    "supervisor_almacen:SuperAlmacen2024!"
    "operario_1:Operario2024!"
)

echo "Testing authentication for all users..."

for user_pass in "${users[@]}"; do
    username=$(echo $user_pass | cut -d: -f1)
    password=$(echo $user_pass | cut -d: -f2)
    
    echo "Testing: $username"
    
    response=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
      -H "Content-Type: application/json" \
      -d "{\"username\": \"$username\", \"password\": \"$password\"}")
    
    if echo "$response" | grep -q "access"; then
        echo "✅ $username: Authentication successful"
    else
        echo "❌ $username: Authentication failed"
        echo "   Response: $response"
    fi
    echo "---"
done
```

### Test Notification Creation by Role

```bash
# Get tokens for different users
ADMIN_TOKEN=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ProvesiAdmin2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

GERENTE_TOKEN=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "gerente", "password": "Gerente2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

# Test notification creation with admin
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Admin Test",
    "message": "Test notification from admin user",
    "priority": "medium"
  }'

# Test notification creation with gerente
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $GERENTE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Manager Test",
    "message": "Test notification from manager user",
    "priority": "medium",
    "targetUser": "empleado@provesi.com"
  }'
```

## Security Best Practices

### Password Requirements

```python
def validate_password_strength(password):
    """Validate password meets security requirements."""
    
    requirements = {
        'length': len(password) >= 12,
        'uppercase': any(c.isupper() for c in password),
        'lowercase': any(c.islower() for c in password),
        'digit': any(c.isdigit() for c in password),
        'special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    }
    
    if all(requirements.values()):
        return True, "Password meets all requirements"
    else:
        failed = [k for k, v in requirements.items() if not v]
        return False, f"Password missing: {', '.join(failed)}"

# Example usage:
valid, message = validate_password_strength("MySecurePass123!")
print(f"Valid: {valid}, Message: {message}")
```

### User Deactivation

```python
def deactivate_user(username, reason=""):
    """Safely deactivate a user."""
    
    # Deactivate Django user
    django_user = User.objects.get(username=username)
    django_user.is_active = False
    django_user.save()
    
    # Note: Keep inventory user for audit trail
    # Don't delete, just mark as inactive if needed
    
    print(f"User {username} deactivated. Reason: {reason}")

def reactivate_user(username):
    """Reactivate a user."""
    
    django_user = User.objects.get(username=username)
    django_user.is_active = True
    django_user.save()
    
    print(f"User {username} reactivated")
```

---

**Note**: Remember to restart the Django application after creating new users to ensure all changes are properly loaded.

**Security Reminder**: Always use strong passwords and consider implementing 2FA for production environments.