"""
API endpoints para autenticación con Auth0.

Provee endpoints para login, logout, validación de tokens
y obtención de información del usuario autenticado.
"""

import json
import requests
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .authentication import get_auth0_user_info
from .permissions import require_auth0_permission


@csrf_exempt
@require_http_methods(["POST"])
def auth_login(request):
    """
    Endpoint para autenticación inicial.
    
    El frontend debe enviar el access_token obtenido de Auth0.
    Este endpoint valida el token y retorna información del usuario.
    
    Body:
    {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    
    Response:
    {
        "success": true,
        "user": {
            "id": "auth0|123456789",
            "email": "usuario@example.com",
            "name": "Usuario Ejemplo"
        },
        "permissions": ["read:pedidos", "write:productos"],
        "message": "Login exitoso"
    }
    """
    try:
        data = json.loads(request.body)
        access_token = data.get('access_token')
        
        if not access_token:
            return JsonResponse({
                'error': 'Token requerido',
                'detail': 'Debe enviar access_token en el body'
            }, status=400)
        
        # Obtener información del usuario desde Auth0
        user_info = get_auth0_user_info(access_token)
        
        # Decodificar el token para obtener permisos
        # (Esto se hace automáticamente en el middleware de autenticación)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False)
            },
            'message': 'Login exitoso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Error de autenticación',
            'detail': str(e)
        }, status=401)


@require_auth0_permission('read:pedidos')
def auth_user_info(request):
    """
    Obtiene información del usuario autenticado actualmente.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Response:
    {
        "success": true,
        "user": {
            "id": "auth0|123456789",
            "email": "usuario@example.com",
            "username": "auth0|123456789"
        },
        "auth": {
            "permissions": ["read:pedidos", "write:productos"],
            "is_admin": false,
            "token_expires": "2023-10-15T12:00:00Z"
        }
    }
    """
    try:
        user = request.user
        auth = getattr(request, 'auth', None)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.username,  # En nuestro caso, username = auth0_id
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat()
            },
            'auth': {
                'permissions': auth.permissions if auth else [],
                'is_admin': auth.is_admin() if auth else False,
                'token': auth.token[:20] + '...' if auth else None  # Solo mostrar inicio del token
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Error obteniendo información del usuario',
            'detail': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def auth_logout(request):
    """
    Endpoint de logout.
    
    En una aplicación stateless con JWT, el logout se maneja 
    principalmente en el frontend eliminando el token.
    
    Este endpoint puede usarse para invalidar el token en Auth0
    o realizar cleanup adicional.
    
    Response:
    {
        "success": true,
        "message": "Logout exitoso"
    }
    """
    try:
        # En una app stateless, no hay mucho que hacer server-side
        # El frontend debe eliminar el token del localStorage/sessionStorage
        
        return JsonResponse({
            'success': True,
            'message': 'Logout exitoso',
            'instructions': 'Elimine el token del almacenamiento local'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Error en logout',
            'detail': str(e)
        }, status=500)


def auth_status(request):
    """
    Verifica el estado de autenticación sin requerir permisos específicos.
    
    Útil para que el frontend verifique si el usuario está autenticado
    sin hacer una llamada que pueda fallar por permisos.
    
    Response (autenticado):
    {
        "authenticated": true,
        "user_id": "auth0|123456789",
        "permissions": ["read:pedidos"]
    }
    
    Response (no autenticado):
    {
        "authenticated": false
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'authenticated': False
        })
    
    auth = getattr(request, 'auth', None)
    
    return JsonResponse({
        'authenticated': True,
        'user_id': request.user.username,
        'permissions': auth.permissions if auth else [],
        'is_admin': auth.is_admin() if auth else False
    })


@require_http_methods(["GET"])
def auth_config(request):
    """
    Proporciona configuración de Auth0 para el frontend.
    
    Response:
    {
        "auth0_domain": "your-tenant.auth0.com",
        "client_id": "your-client-id",
        "audience": "https://api.your-app.com"
    }
    """
    return JsonResponse({
        'auth0_domain': settings.AUTH0_DOMAIN,
        'client_id': settings.AUTH0_CLIENT_ID,
        'audience': settings.AUTH0_AUDIENCE,
        'redirect_uri': f'{request.scheme}://{request.get_host()}/auth/callback'
    })