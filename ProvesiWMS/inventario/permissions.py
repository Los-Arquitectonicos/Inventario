"""
Sistema de permisos basado en Auth0 scopes.

Define decoradores y clases de permisos para proteger endpoints
según los scopes/permisos definidos en Auth0.
"""

from functools import wraps
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes


class Auth0Permission(permissions.BasePermission):
    """
    Clase base para permisos basados en Auth0 scopes.
    """
    required_permissions = []
    
    def has_permission(self, request, view):
        """
        Verifica si el usuario tiene los permisos requeridos.
        """
        if not request.user.is_authenticated:
            return False
            
        auth = getattr(request, 'auth', None)
        if not auth:
            return False
            
        # Verificar permisos específicos
        for permission in self.required_permissions:
            if not auth.has_permission(permission):
                return False
                
        return True


class ReadPedidosPermission(Auth0Permission):
    """Permiso para leer pedidos."""
    required_permissions = ['read:pedidos']


class WritePedidosPermission(Auth0Permission):
    """Permiso para crear/modificar pedidos."""
    required_permissions = ['write:pedidos']


class DeletePedidosPermission(Auth0Permission):
    """Permiso para eliminar pedidos."""
    required_permissions = ['delete:pedidos']


class ReadProductosPermission(Auth0Permission):
    """Permiso para leer productos."""
    required_permissions = ['read:productos']


class WriteProductosPermission(Auth0Permission):
    """Permiso para crear/modificar productos."""
    required_permissions = ['write:productos']


class ReadBodegasPermission(Auth0Permission):
    """Permiso para leer bodegas."""
    required_permissions = ['read:bodegas']


class WriteBodegasPermission(Auth0Permission):
    """Permiso para crear/modificar bodegas."""
    required_permissions = ['write:bodegas']


class AdminPermission(Auth0Permission):
    """Permiso de administrador (acceso total)."""
    required_permissions = ['admin:all']
    
    def has_permission(self, request, view):
        """
        Admin tiene acceso total, o verificar permiso específico.
        """
        if not request.user.is_authenticated:
            return False
            
        auth = getattr(request, 'auth', None)
        if not auth:
            return False
            
        # Admin tiene acceso total
        if auth.is_admin():
            return True
            
        # Si no es admin, verificar permisos específicos
        return super().has_permission(request, view)


def require_auth0_permission(permission):
    """
    Decorador para proteger vistas basado en permisos Auth0.
    
    Args:
        permission (str): Permiso requerido (ej: 'read:pedidos')
        
    Usage:
        @require_auth0_permission('read:pedidos')
        def listar_pedidos(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Verificar autenticación
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticación requerida',
                    'detail': 'Debe incluir un token JWT válido en el header Authorization'
                }, status=401)
            
            # Verificar permisos
            auth = getattr(request, 'auth', None)
            if not auth:
                return JsonResponse({
                    'error': 'Token inválido',
                    'detail': 'No se pudo extraer información de autenticación del token'
                }, status=401)
            
            # Verificar permiso específico o admin
            if not (auth.has_permission(permission) or auth.is_admin()):
                return JsonResponse({
                    'error': 'Permisos insuficientes',
                    'detail': f'Se requiere el permiso: {permission}',
                    'required_permission': permission,
                    'user_permissions': auth.permissions
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_any_auth0_permission(*permissions):
    """
    Decorador que requiere AL MENOS UNO de los permisos especificados.
    
    Args:
        *permissions: Lista de permisos (ej: 'read:pedidos', 'admin:all')
        
    Usage:
        @require_any_auth0_permission('read:pedidos', 'admin:all')
        def ver_pedido(request, pedido_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Verificar autenticación
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticación requerida'
                }, status=401)
            
            # Verificar permisos
            auth = getattr(request, 'auth', None)
            if not auth:
                return JsonResponse({
                    'error': 'Token inválido'
                }, status=401)
            
            # Verificar si tiene alguno de los permisos
            if not auth.has_any_permission(permissions):
                return JsonResponse({
                    'error': 'Permisos insuficientes',
                    'detail': f'Se requiere al menos uno de: {", ".join(permissions)}',
                    'required_permissions': list(permissions),
                    'user_permissions': auth.permissions
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorador que requiere permisos de administrador.
    
    Usage:
        @admin_required
        def eliminar_todos_productos(request):
            ...
    """
    return require_auth0_permission('admin:all')(view_func)