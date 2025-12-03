# 🚀 GUÍA RÁPIDA - AWS CLOUDSHELL

## Para desplegar TODA la infraestructura en 5 minutos:

### 1. Abre AWS CloudShell
- Vai a: https://console.aws.amazon.com
- Busca "CloudShell" en la barra superior
- Haz click en el ícono (>_)

### 2. Ejecuta estos comandos:
```bash
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario
git checkout notificaciones
cd terraform
./deploy_complete_infrastructure.sh
```

### 3. Espera y confirma
- El script instalará Terraform automáticamente
- Te pedirá confirmación antes de crear la infraestructura
- Escribe `yes` cuando lo pida

### 4. ¡Listo!
- La infraestructura estará disponible en ~10-15 minutos
- Al final verás las URLs para probar las APIs

## ⚠️ Para destruir todo después:
```bash
./cleanup_infrastructure.sh
```

## 💡 URLs que obtendrás:
- **API Principal**: http://tu-alb.amazonaws.com/api/
- **Notificaciones**: http://tu-alb.amazonaws.com/notifications/
- **Kong Admin**: http://kong-ip:8001/

---
**Costo estimado**: ~$150/mes (recuerda apagar cuando no uses)