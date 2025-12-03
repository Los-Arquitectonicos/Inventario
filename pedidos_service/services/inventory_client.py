"""
Cliente HTTP para comunicarse con Django InventarioWMS
"""
import httpx
import logging
from typing import Optional, Dict, Any
from pedidos_service.config import settings
from pedidos_service.schemas.order import ProductInfo

logger = logging.getLogger(__name__)


class InventoryClient:
    """Cliente para interactuar con el API de Django"""
    
    def __init__(self):
        self.base_url = settings.DJANGO_API_URL
        self.timeout = 10.0  # 10 segundos timeout
        
    async def get_product(self, producto_id: int) -> Optional[ProductInfo]:
        """
        Obtener información de un producto desde Django
        
        Args:
            producto_id: ID del producto
            
        Returns:
            ProductInfo si existe, None si no se encuentra
            
        Raises:
            httpx.HTTPError: Error de comunicación
        """
        url = f"{self.base_url}/api/productos/{producto_id}/"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    logger.warning(f"Producto {producto_id} no encontrado en Django")
                    return None
                    
                response.raise_for_status()
                data = response.json()
                
                # Mapear respuesta de Django a nuestro schema
                return ProductInfo(
                    id=data["id"],
                    nombre=data["nombre"],
                    precio=float(data.get("precio", 0)),
                    stock_disponible=int(data.get("stock", 0))
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Error al consultar producto {producto_id}: {e}")
            raise
            
    async def get_cliente(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener información de un cliente desde Django
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Dict con nombre y email si existe, None si no se encuentra
            
        Raises:
            httpx.HTTPError: Error de comunicación
        """
        url = f"{self.base_url}/api/clientes/{cliente_id}/"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    logger.warning(f"Cliente {cliente_id} no encontrado en Django")
                    return None
                    
                response.raise_for_status()
                data = response.json()
                
                return {
                    "nombre": data.get("nombre", ""),
                    "email": data.get("email", "")
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Error al consultar cliente {cliente_id}: {e}")
            raise
            
    async def check_health(self) -> bool:
        """
        Verificar conectividad con Django
        
        Returns:
            True si Django está disponible, False si no
        """
        url = f"{self.base_url}/health/"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except httpx.HTTPError:
            return False
