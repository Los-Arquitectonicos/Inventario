"""
Decoradores y utilidades de autenticación para ProvesiWMS.
Proporciona control de acceso basado en roles y autenticación JWT.
"""

import logging
import jwt
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('inventario')

# Definición de roles y sus permisos
ROLE_PERMISSIONS = {
    'admin': {
        'can_create_users': True,
        'can_delete_users': True,
        'can_modify_all_data': True,
        'can_view_all_data': True,
        'can_access_reports': True,
        'can_manage_inventory': True,
        'can_manage_orders': True,
        'can_manage_clients': True,
        'can_manage_warehouses': True,
    },
    'gerente': {
        'can_create_users': False,
        'can_delete_users': False,
        'can_modify_all_data': True,
        'can_view_all_data': True,
        'can_access_reports': True,
        'can_manage_inventory': True,
        'can_manage_orders': True,
        'can_manage_clients': True,
        'can_manage_warehouses': True,
    },
    'supervisor': {
        'can_create_users': False,
        'can_delete_users': False,
        'can_modify_all_data': False,
        'can_view_all_data': True,
        'can_access_reports': True,
        'can_manage_inventory': True,
        'can_manage_orders': True,
        'can_manage_clients': False,
        'can_manage_warehouses': False,
    },
    'empleado': {
        'can_create_users': False,
        'can_delete_users': False,
        'can_modify_all_data': False,
        'can_view_all_data': False,
        'can_access_reports': False,
        'can_manage_inventory': False,
        'can_manage_orders': False,
        'can_manage_clients': False,
        'can_manage_warehouses': False,
    }
}

def get_user_role(user):
    """
    Obtiene el rol de un usuario desde el modelo de inventario.
    
    Args:
        user: Usuario de Django Auth
    
    Returns:
        str: Rol del usuario ('admin', 'gerente', 'supervisor', 'empleado')
    """
    if user.is_superuser:
        return 'admin'
    
    try:
        from inventario.models import Usuario
        usuario_inventario = Usuario.objects.get(nombre_usuario=user.username)
        return usuario_inventario.rol
    except Exception:  # Catch all exceptions including Usuario.DoesNotExist
        return 'empleado'  # Rol por defecto

def has_permission(user, permission):
    """
    Verifica si un usuario tiene un permiso específico.
    
    Args:
        user: Usuario de Django Auth
        permission: Nombre del permiso a verificar
    
    Returns:
        bool: True si el usuario tiene el permiso
    """
    if not user.is_authenticated:
        return False
    
    role = get_user_role(user)
    permissions = ROLE_PERMISSIONS.get(role, {})
    return permissions.get(permission, False)

def require_permission(permission):
    """
    Decorador que requiere un permiso específico para acceder a la vista.
    
    Args:
        permission: Nombre del permiso requerido
    
    Usage:
        @require_permission('can_manage_orders')
        def my_view(request):
            # Solo usuarios con permiso 'can_manage_orders' pueden acceder
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }, status=401)
            
            if not has_permission(request.user, permission):
                user_role = get_user_role(request.user)
                logger.warning(f"Usuario {request.user.username} ({user_role}) intentó acceder sin permiso: {permission}")
                return JsonResponse({
                    'success': False,
                    'error': f'No tienes permiso para realizar esta acción. Permiso requerido: {permission}',
                    'code': 'PERMISSION_DENIED',
                    'required_permission': permission,
                    'user_role': user_role
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_roles(*allowed_roles):
    """
    Decorador que requiere uno de los roles especificados.
    
    Args:
        *allowed_roles: Roles permitidos para acceder a la vista
    
    Usage:
        @require_roles('admin', 'gerente')
        def admin_view(request):
            # Solo admins y gerentes pueden acceder
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }, status=401)
            
            user_role = get_user_role(request.user)
            
            if user_role not in allowed_roles:
                logger.warning(f"Usuario {request.user.username} ({user_role}) intentó acceder con rol no autorizado. Roles permitidos: {allowed_roles}")
                return JsonResponse({
                    'success': False,
                    'error': f'Acceso denegado. Roles permitidos: {", ".join(allowed_roles)}',
                    'code': 'ROLE_NOT_ALLOWED',
                    'allowed_roles': list(allowed_roles),
                    'user_role': user_role
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def api_require_permission(permission):
    """
    Decorador para vistas de API que requiere un permiso específico.
    Compatible con Django REST Framework.
    
    Args:
        permission: Nombre del permiso requerido
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not has_permission(request.user, permission):
                user_role = get_user_role(request.user)
                logger.warning(f"Usuario {request.user.username} ({user_role}) intentó acceder API sin permiso: {permission}")
                return Response({
                    'success': False,
                    'error': f'No tienes permiso para realizar esta acción. Permiso requerido: {permission}',
                    'code': 'PERMISSION_DENIED',
                    'required_permission': permission,
                    'user_role': user_role
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def api_require_roles(*allowed_roles):
    """
    Decorador para vistas de API que requiere uno de los roles especificados.
    Compatible con Django REST Framework.
    
    Args:
        *allowed_roles: Roles permitidos para acceder a la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user_role = get_user_role(request.user)
            
            if user_role not in allowed_roles:
                logger.warning(f"Usuario {request.user.username} ({user_role}) intentó acceder API con rol no autorizado. Roles permitidos: {allowed_roles}")
                return Response({
                    'success': False,
                    'error': f'Acceso denegado. Roles permitidos: {", ".join(allowed_roles)}',
                    'code': 'ROLE_NOT_ALLOWED',
                    'allowed_roles': list(allowed_roles),
                    'user_role': user_role
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def jwt_required(view_func):
    """
    Decorador que requiere autenticación JWT válida.
    
    Usage:
        @jwt_required
        def my_view(request):
            # Usuario autenticado via JWT
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener el token del header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({
                'success': False,
                'error': 'Token JWT requerido',
                'code': 'JWT_REQUIRED'
            }, status=401)
        
        # Extraer el token del header "Bearer <token>"
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return JsonResponse({
                'success': False,
                'error': 'Formato de token inválido',
                'code': 'INVALID_TOKEN_FORMAT'
            }, status=401)
        
        # Validar el token JWT
        try:
            # Decodificar el token usando la SECRET_KEY de Django
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Token JWT inválido',
                    'code': 'INVALID_TOKEN'
                }, status=401)
            
            # Obtener el usuario
            user = User.objects.get(id=user_id)
            request.user = user
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'success': False,
                'error': 'Token JWT expirado',
                'code': 'TOKEN_EXPIRED'
            }, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({
                'success': False,
                'error': 'Token JWT inválido',
                'code': 'INVALID_TOKEN'
            }, status=401)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no encontrado',
                'code': 'USER_NOT_FOUND'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def get_user_permissions(user):
    """
    Obtiene todos los permisos de un usuario basado en su rol.
    
    Args:
        user: Usuario de Django Auth
    
    Returns:
        dict: Diccionario con todos los permisos del usuario
    """
    role = get_user_role(user)
    return ROLE_PERMISSIONS.get(role, {})

class AuthenticationMixin(View):
    """
    Mixin que se puede usar con vistas basadas en clases para agregar autenticación.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Autenticación requerida',
                'code': 'AUTH_REQUIRED'
            }, status=401)
        return super().dispatch(request, *args, **kwargs)

class PermissionMixin(View):
    """
    Mixin que requiere un permiso específico para vistas basadas en clases.
    
    Usage:
        class MyView(PermissionMixin, View):
            required_permission = 'can_manage_orders'
    """
    required_permission = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Autenticación requerida',
                'code': 'AUTH_REQUIRED'
            }, status=401)
        
        if self.required_permission and not has_permission(request.user, self.required_permission):
            user_role = get_user_role(request.user)
            return JsonResponse({
                'success': False,
                'error': f'No tienes permiso para realizar esta acción. Permiso requerido: {self.required_permission}',
                'code': 'PERMISSION_DENIED',
                'required_permission': self.required_permission,
                'user_role': user_role
            }, status=403)
        
        return super().dispatch(request, *args, **kwargs)

def log_access_attempt(request, resource, action, success=True):
    """
    Registra intentos de acceso para auditoría.
    
    Args:
        request: Request object
        resource: Recurso al que se está accediendo
        action: Acción que se está realizando
        success: Si el acceso fue exitoso o no
    """
    user = request.user
    if user.is_authenticated:
        user_role = get_user_role(user)
        logger.info(f"Acceso {'exitoso' if success else 'denegado'}: Usuario {user.username} ({user_role}) - Recurso: {resource} - Acción: {action}")
    else:
        logger.warning(f"Intento de acceso no autenticado - Recurso: {resource} - Acción: {action} - IP: {request.META.get('REMOTE_ADDR')}")