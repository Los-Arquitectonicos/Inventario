"""
Auth0 JWT Authentication para Django REST Framework.

Implementa autenticación JWT usando tokens de Auth0.
Valida tokens, extrae permisos y autentica usuarios.
"""

import json
import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    """
    Autenticación JWT usando Auth0.
    
    Valida tokens JWT enviados en el header Authorization.
    Extrae información del usuario y permisos desde el token.
    """
    
    def authenticate(self, request):
        """
        Autentica la request usando JWT token de Auth0.
        
        Returns:
            (user, auth) tuple si es válido
            None si no hay token o no es válido
        """
        auth_header = get_authorization_header(request).split()
        
        if not auth_header or auth_header[0].lower() != b'bearer':
            return None
            
        if len(auth_header) != 2:
            return None
            
        token = auth_header[1].decode('utf-8')
        
        try:
            # Validar y decodificar el token
            payload = self._verify_token(token)
            
            # Extraer información del usuario
            user = self._get_or_create_user(payload)
            
            # Extraer permisos
            permissions = payload.get('permissions', [])
            
            # Crear objeto de autenticación
            auth = Auth0Authentication(user, token, permissions)
            
            return (user, auth)
            
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token inválido: {str(e)}')
    
    def _verify_token(self, token):
        """
        Verifica y decodifica el JWT token usando la clave pública de Auth0.
        """
        # Obtener clave pública de Auth0
        jwks_url = f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json'
        jwks_client = jwt.PyJWKClient(jwks_url)
        
        try:
            # Obtener la clave de firma
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Decodificar y validar el token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=settings.AUTH0_AUDIENCE,
                issuer=f'https://{settings.AUTH0_DOMAIN}/'
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Token inválido: {str(e)}')
    
    def _get_or_create_user(self, payload):
        """
        Obtiene o crea un usuario Django basado en el payload del JWT.
        """
        auth0_id = payload.get('sub')
        email = payload.get('email', '')
        username = payload.get('preferred_username') or email or auth0_id
        
        # Buscar usuario existente
        try:
            user = User.objects.get(username=auth0_id)
        except User.DoesNotExist:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=auth0_id,
                email=email,
                first_name=payload.get('given_name', ''),
                last_name=payload.get('family_name', '')
            )
        
        return user


class Auth0Authentication:
    """
    Objeto de autenticación que contiene información del usuario y permisos.
    """
    
    def __init__(self, user, token, permissions):
        self.user = user
        self.token = token
        self.permissions = permissions
    
    def has_permission(self, permission):
        """
        Verifica si el usuario tiene un permiso específico.
        """
        return permission in self.permissions
    
    def has_any_permission(self, permissions):
        """
        Verifica si el usuario tiene alguno de los permisos especificados.
        """
        return any(perm in self.permissions for perm in permissions)
    
    def is_admin(self):
        """
        Verifica si el usuario tiene permisos de administrador.
        """
        return 'admin:all' in self.permissions


def get_auth0_user_info(access_token):
    """
    Obtiene información detallada del usuario desde Auth0.
    
    Args:
        access_token: Token de acceso de Auth0
        
    Returns:
        dict: Información del usuario
    """
    url = f'https://{settings.AUTH0_DOMAIN}/userinfo'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f'Error obteniendo información del usuario: {str(e)}')