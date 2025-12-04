"""
Cliente HTTP para validar datos con ProvesiWMS
"""
import os
import requests
import logging
from typing import Optional, Dict
import urllib3

# Desactivar warnings de SSL para certificados self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger()

PROVESI_API_URL = os.environ.get('PROVESI_API_URL', 'http://localhost:8080')
PROVESI_TIMEOUT = 10


def validate_producto(producto_id: int) -> Optional[Dict]:
    """
    Validar que un producto existe en ProvesiWMS
    
    Returns:
        Dict con {id, nombre, precio, stock} o None si no existe
    """
    try:
        url = f"{PROVESI_API_URL}/api/productos/{producto_id}/"
        response = requests.get(url, timeout=PROVESI_TIMEOUT, verify=False)
        
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
        url = f"{PROVESI_API_URL}/api/clientes/{cliente_id}/"
        response = requests.get(url, timeout=PROVESI_TIMEOUT, verify=False)
        
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
