# Guía Wireshark para Anti-Sniffing - ProvesiWMS

## Objetivo
Usar Wireshark directamente para validar: *"el atacante no pueda ver la informacion en texto plano"*

## Archivos Creados
- `generar_trafico_wireshark.sh` - Script para generar tráfico mientras capturas
- `checklist_wireshark_anti_sniffing.md` - Checklist de validación completo

## Procedimiento Rápido

### 1. Preparación
```bash
# Instalar Wireshark
brew install wireshark  # macOS
sudo apt install wireshark  # Linux

# Ir al directorio de pruebas
cd tests/anti_sniffing
```

### 2. Captura
1. **Abrir Wireshark**: `wireshark`
2. **Seleccionar interfaz**: WiFi/Ethernet
3. **Aplicar filtro**: `host provesi-alb-2003818714.us-east-1.elb.amazonaws.com`
4. **Iniciar captura**: Click en botón rojo
5. **Generar tráfico**: `./generar_trafico_wireshark.sh`
6. **Detener captura**: Ctrl+E

### 3. Análisis Anti-Sniffing

#### Filtros Críticos:
```bash
# 1. Verificar redirección HTTPS
http and host provesi-alb-2003818714.us-east-1.elb.amazonaws.com

# 2. Analizar handshake TLS  
tls.handshake.type == 1

# 3. Buscar texto plano (¡NO debe haber resultados!)
tcp contains "password" or tcp contains "admin"

# 4. Ver tráfico cifrado
tls

# 5. Detectar protocolos inseguros
tls.handshake.version == 0x0301  # TLS 1.0
```

### 4. Validación
Usar el checklist en `checklist_wireshark_anti_sniffing.md`

## Resultados Esperados
- ✅ **Solo tráfico HTTPS cifrado**
- ✅ **Redirección HTTP → HTTPS**
- ✅ **TLS 1.2/1.3 únicamente**
- ✅ **Sin datos en texto plano**
- ✅ **Certificados válidos**

## Señales de Alerta
- 🚨 **Datos legibles en SSL Stream**
- 🚨 **TLS < 1.2 aceptado**
- 🚨 **Cipher suites débiles**
- 🚨 **Respuestas HTTP 200**

## Ventajas de Wireshark vs Scripts
| Aspecto | Scripts | Wireshark |
|---------|---------|-----------|
| **Profundidad** | Headers superficiales | Análisis completo de paquetes |
| **Detección** | Básica | Downgrade attacks, MITM, timing |
| **Evidencia** | Logs de texto | Captura .pcap forensic |
| **Análisis** | Automatizado | Manual pero exhaustivo |

## Conclusión
Wireshark proporciona **análisis forense completo** que revela vulnerabilidades invisibles para scripts básicos. Es **esencial** para validación de seguridad anti-sniffing real.

---
**Última actualización**: $(date)
**Autor**: Equipo de Seguridad ProvesiWMS