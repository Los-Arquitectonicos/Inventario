"""
Cliente HTTP para validar datos con ProvesiWMS
"""
import os
import requests
import logging
from typing import Optional, Dict
import urllib3
from datetime import datetime, timedelta

# Desactivar warnings de SSL para certificados self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger()

PROVESI_API_URL = os.environ.get('PROVESI_API_URL', 'http://localhost:8080')
PROVESI_TIMEOUT = 10
PROVESI_USER = os.environ.get('PROVESI_USER', 'admin')
PROVESI_PASSWORD = os.environ.get('PROVESI_PASSWORD', 'admin123')

# Cache del token JWT
_jwt_token = None
_token_expiry = None


def get_jwt_token() -> str:
    """
    Obtener token JWT de ProvesiWMS (con cache)
    
    Returns:
        Token JWT válido
    """
    global _jwt_token, _token_expiry
    
    # Si tenemos un token válido en cache, usarlo
    if _jwt_token and _token_expiry and datetime.now() < _token_expiry:
        return _jwt_token
    
    # Obtener nuevo token
    try:
        url = f"{PROVESI_API_URL}/inventario/auth/login/"
        data = {
            "username": PROVESI_USER,
            "password": PROVESI_PASSWORD
        }
        
        response = requests.post(url, json=data, timeout=PROVESI_TIMEOUT, verify=False)
        response.raise_for_status()
        
        json_data = response.json()
        _jwt_token = json_data.get('access')
        
        if not _jwt_token:
            raise Exception("No se recibió token JWT en la respuesta")
        
        # Cache por 50 minutos (los tokens duran 60 minutos)
        _token_expiry = datetime.now() + timedelta(minutes=50)
        
        logger.info("Token JWT obtenido correctamente")
        return _jwt_token
        
    except Exception as e:
        logger.error(f"Error obteniendo token JWT: {e}")
        raise Exception(f"No se pudo autenticar con ProvesiWMS: {str(e)}")


def validate_producto(producto_id: int) -> Optional[Dict]:
    """
    Validar que un producto existe en ProvesiWMS
    
    Returns:
        Dict con {id, nombre, precio, stock} o None si no existe
    """
    try:
        token = get_jwt_token()
        url = f"{PROVESI_API_URL}/inventario/api/productos/{producto_id}/"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers, timeout=PROVESI_TIMEOUT, verify=False)
        
        if response.status_code == 404:
            logger.warning(f"Producto {producto_id} no encontrado")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": data["id"],
            "nombre": data["nombre"],
            "precio": float(data.get("precio", 0)),
            "stock": int(data.get("stock", 0))
        }
        
    except requests.RequestException as e:
        logger.error(f"Error al validar producto {producto_id}: {e}")
        raise Exception(f"Error de comunicación con ProvesiWMS: {str(e)}")


def validate_cliente(cliente_id: int) -> Optional[Dict]:
    """
    Validar que un cliente existe en ProvesiWMS
    
    Returns:
        Dict con {id, nombre, email} o None si no existe
    """
    try:
        token = get_jwt_token()
        url = f"{PROVESI_API_URL}/inventario/api/clientes/{cliente_id}/"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers, timeout=PROVESI_TIMEOUT, verify=False)
        
        if response.status_code == 404:
            logger.warning(f"Cliente {cliente_id} no encontrado")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": data["id"],
            "nombre": data.get("nombre", ""),
            "email": data.get("email", "")
        }
        
    except requests.RequestException as e:
        logger.error(f"Error al validar cliente {cliente_id}: {e}")
        raise Exception(f"Error de comunicación con ProvesiWMS: {str(e)}")
