"""
Vistas de autenticación para ProvesiWMS.
Implementa login/logout con JWT tokens y gestión de usuarios.
"""

import logging
from datetime import datetime, timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import json

logger = logging.getLogger('inventario')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado para JWT que incluye información adicional del usuario.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información adicional del usuario
        user = self.user
        
        if user is None:
            raise ValueError("Usuario no encontrado")
        
        # Obtener o crear el Usuario del modelo de inventario
        from inventario.models import Usuario
        try:
            usuario_inventario = Usuario.objects.get(nombre_usuario=user.username)
            user_role = usuario_inventario.rol
            user_id_inventario = usuario_inventario.pk
        except Usuario.DoesNotExist:
            # Si no existe en el modelo inventario, crear uno básico
            usuario_inventario = Usuario.objects.create(
                nombre_usuario=user.username,
                email=user.email,
                rol='empleado'
            )
            user_role = 'empleado'
            user_id_inventario = usuario_inventario.pk
            
        user_data = {
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'inventario_user_id': user_id_inventario,
                'role': user_role,
            },
            'login_time': datetime.now(timezone.utc).isoformat()
        }
        
        data.update(user_data)
        
        # Registrar el login
        logger.info(f"Usuario {user.username} ({user_role}) ha iniciado sesión")
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT con información adicional."""
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Vista de login que retorna tokens JWT.
    
    POST /auth/login/
    {
        "username": "admin",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user": { ... },
        "expires_in": 3600
    }
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'error': 'Username y password son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Crear tokens JWT
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                
                # Obtener información del usuario del inventario
                from inventario.models import Usuario
                try:
                    usuario_inventario = Usuario.objects.get(nombre_usuario=user.username)
                    user_role = usuario_inventario.rol
                    user_id_inventario = usuario_inventario.pk
                except Usuario.DoesNotExist:
                    # Crear usuario en inventario si no existe
                    usuario_inventario = Usuario.objects.create(
                        nombre_usuario=user.username,
                        email=user.email,
                        rol='empleado'
                    )
                    user_role = 'empleado'
                    user_id_inventario = usuario_inventario.pk
                
                # Actualizar último acceso
                usuario_inventario.ultimo_acceso = datetime.now(timezone.utc)
                usuario_inventario.save()
                
                response_data = {
                    'success': True,
                    'message': f'Login exitoso para {username}',
                    'access': str(access),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.pk,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'inventario_user_id': user_id_inventario,
                        'role': user_role,
                    },
                    'expires_in': 3600,  # 1 hora
                    'login_time': datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Login exitoso: {username} ({user_role})")
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Intento de login con usuario inactivo: {username}")
                return Response({
                    'success': False,
                    'error': 'Cuenta de usuario desactivada'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.warning(f"Intento de login fallido: {username}")
            return Response({
                'success': False,
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Vista de logout que invalida el refresh token.
    
    POST /auth/logout/
    Headers: Authorization: Bearer <access_token>
    {
        "refresh": "jwt_refresh_token"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Logout exitoso para usuario: {request.user.username}")
                return Response({
                    'success': True,
                    'message': 'Logout exitoso'
                }, status=status.HTTP_200_OK)
            except TokenError:
                logger.warning(f"Token inválido en logout para usuario: {request.user.username}")
                return Response({
                    'success': False,
                    'error': 'Token inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Logout sin refresh token (solo invalida la sesión actual)
            logger.info(f"Logout sin refresh token para usuario: {request.user.username}")
            return Response({
                'success': True,
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Obtiene el perfil del usuario autenticado.
    
    GET /auth/profile/
    Headers: Authorization: Bearer <access_token>
    """
    try:
        user = request.user
        
        # Obtener información del modelo de inventario
        from inventario.models import Usuario
        try:
            usuario_inventario = Usuario.objects.get(nombre_usuario=user.username)
        except Usuario.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado en el sistema de inventario'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'inventario_profile': {
                    'id': usuario_inventario.pk,
                    'role': usuario_inventario.rol,
                    'telefono': usuario_inventario.telefono,
                    'ultimo_acceso': usuario_inventario.ultimo_acceso.isoformat(),
                    'fecha_creacion': usuario_inventario.fecha_creacion.isoformat()
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verifica si un token JWT es válido.
    
    POST /auth/verify/
    {
        "token": "jwt_access_token"
    }
    """
    try:
        token = request.data.get('token')
        
        if not token:
            return Response({
                'success': False,
                'error': 'Token es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verificar token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Obtener usuario
            user = User.objects.get(id=user_id)
            
            return Response({
                'success': True,
                'valid': True,
                'user': {
                    'id': user.pk,
                    'username': user.username,
                    'email': user.email,
                },
                'token_type': access_token['token_type'],
                'expires': access_token['exp']
            }, status=status.HTTP_200_OK)
            
        except (TokenError, InvalidToken, User.DoesNotExist):
            return Response({
                'success': False,
                'valid': False,
                'error': 'Token inválido o expirado'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Cambio de contraseña del usuario autenticado.
    
    POST /auth/change-password/
    Headers: Authorization: Bearer <access_token>
    {
        "current_password": "password_actual",
        "new_password": "nueva_password"
    }
    """
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response({
                'success': False,
                'error': 'current_password y new_password son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Verificar contraseña actual
        if not user.check_password(current_password):
            return Response({
                'success': False,
                'error': 'Contraseña actual incorrecta'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar nueva contraseña (mínimo 8 caracteres)
        if len(new_password) < 8:
            return Response({
                'success': False,
                'error': 'La nueva contraseña debe tener al menos 8 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cambiar contraseña
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Cambio de contraseña exitoso para usuario: {user.username}")
        
        return Response({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)