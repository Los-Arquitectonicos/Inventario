# 🔒 Validación Anti-Sniffing con Wireshark - ProvesiWMS

**Objetivo**: Verificar que "el atacante no pueda ver la información en texto plano"

## 📋 Descripción

Este módulo contiene herramientas especializadas para validar la seguridad contra ataques de sniffing de red utilizando análisis de captura de paquetes estilo Wireshark. El objetivo es asegurar que ningún atacante pueda interceptar y leer información sensible en texto plano.

## 🎯 Objetivo Principal

**Requisito de Seguridad**: *"el atacante no pueda ver la información en texto plano"*

Las herramientas verifican que:
- Todas las comunicaciones estén cifradas (HTTPS/TLS)
- Los datos se transmitan como "Application Data" encriptado
- No existan vulnerabilidades en handshakes TLS
- Los certificados y cadenas de confianza sean válidos

## 🛠️ Herramientas Incluidas

### 1. **Generador de Tráfico para Wireshark**
- **Archivo**: `generar_trafico_wireshark.sh`
- **Uso**: Genera patrones de tráfico para capturar con Wireshark
- **Función**: Simula diferentes escenarios (HTTP, HTTPS, autenticación)

### 2. **Análisis Avanzado Nivel Wireshark**
- **Archivo**: `test_anti_sniffing_wireshark_level.sh`
- **Función**: Análisis profundo de protocolos y vulnerabilidades
- **Incluye**: Handshakes TLS, análisis de certificados, detección de downgrade attacks

### 3. **Documentación y Checklists**
- **Guía**: `GUIA_WIRESHARK.md` - Tutorial completo de uso
- **Checklist**: `checklist_wireshark_anti_sniffing.md` - Lista de verificación
- **Análisis**: `analisis_wireshark_resultados.md` - Interpretación de resultados

## 🚀 Uso Rápido

### Opción 1: Análisis con Wireshark Real
```bash
# 1. Abrir Wireshark y comenzar captura
sudo wireshark

# 2. Generar tráfico para análisis
./generar_trafico_wireshark.sh

# 3. Analizar paquetes capturados
# Ver: checklist_wireshark_anti_sniffing.md
```

### Opción 2: Análisis Automatizado Avanzado
```bash
# Ejecutar análisis completo estilo Wireshark
./test_anti_sniffing_wireshark_level.sh
```

## 📊 Tipos de Análisis

### 🔍 **Análisis de Paquetes**
- Inspección de handshakes TLS
- Verificación de encriptación de datos
- Análisis de certificados SSL
- Detección de vulnerabilidades de protocolo

### 🛡️ **Validaciones de Seguridad**
- Forzado de HTTPS
- Headers de seguridad
- Configuración TLS/SSL
- Prevención de downgrade attacks

### 📈 **Reportes Generados**
- Análisis detallado de vulnerabilidades
- Cadenas de certificados
- Resumen ejecutivo de seguridad
- Recomendaciones de mejora

## 📁 Estructura de Archivos

```
anti_sniffing/
├── generar_trafico_wireshark.sh          # Generador de tráfico
├── test_anti_sniffing_wireshark_level.sh # Análisis avanzado  
├── GUIA_WIRESHARK.md                     # Tutorial completo
├── checklist_wireshark_anti_sniffing.md  # Lista verificación
├── analisis_wireshark_resultados.md      # Interpretación resultados
└── wireshark_level_*/                    # Resultados de análisis
```

## ✅ Resultados Esperados

### **Sistema Seguro:**
- ✅ Todo el tráfico encriptado (TLS/HTTPS)
- ✅ Datos como "Application Data" 
- ✅ Handshakes TLS exitosos
- ✅ Certificados válidos

### **Información NO Visible:**
- ❌ Credenciales de usuario
- ❌ Datos de aplicación (JSON)
- ❌ Tokens de sesión
- ❌ Contenido de páginas

## 🔧 Requisitos

- **Sistema**: macOS/Linux con permisos de red
- **Herramientas**: curl, openssl, tcpdump
- **Opcional**: Wireshark para análisis manual
- **Red**: Conectividad a AWS (provesi-alb-*)

## 📚 Documentación

- `GUIA_WIRESHARK.md`: Tutorial paso a paso para usar Wireshark
- `checklist_wireshark_anti_sniffing.md`: Lista de verificación manual
- `analisis_wireshark_resultados.md`: Interpretación de resultados

## 🎯 Validación del Requisito

**Requisito**: *"el atacante no pueda ver la información en texto plano"*

**✅ CUMPLIDO SI:**
- Ningún dato sensible visible en captura de paquetes
- Todo el contenido aparece como "Application Data" encriptado
- Handshakes TLS completos y seguros

**❌ NO CUMPLIDO SI:**
- Datos visibles en texto plano
- Fallas en handshakes TLS
- Exposición de credenciales o tokens

## 🔍 Análisis Manual con Wireshark

### Instalación de Wireshark
```bash
# macOS
brew install wireshark

# Permisos de captura
sudo dseditgroup -o edit -a whoami -t user access_bpf
```

### Uso Básico
1. **Iniciar captura**: `sudo wireshark`
2. **Generar tráfico**: `./generar_trafico_wireshark.sh`
3. **Aplicar filtros**: `host provesi-alb-2003818714.us-east-1.elb.amazonaws.com`
4. **Analizar protocolos**: TLS handshakes, Application Data

### Filtros Útiles
```
# Solo tráfico HTTPS
tcp.port == 443

# Solo handshakes TLS
tls.handshake.type

# Datos encriptados
tls.app_data
```

## 🛠️ Solución de Problemas

### Permisos de Wireshark
```bash
# Instalar ChmodBPF para macOS
curl https://bugs.wireshark.org/bugzilla/attachment.cgi?id=3373 -o ChmodBPF_Install.pkg
sudo installer -pkg ChmodBPF_Install.pkg -target /
```

### Conectividad
```bash
# Verificar conectividad
curl -I https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com/inventario/
```

### Dependencias
```bash
# Verificar herramientas
which curl openssl tcpdump
```

## 📊 Interpretación de Resultados

### ✅ **Sistema Protegido**
```
Estado: SEGURO
- Handshakes TLS exitosos
- Application Data encriptado
- Certificados válidos
- Sin exposición de datos
```

### ❌ **Sistema Vulnerable**
```
Estado: VULNERABLE
- Datos en texto plano detectados
- Fallas en TLS
- Certificados inválidos
- Exposición de información sensible
```

---

*Herramientas especializadas para validación anti-sniffing con análisis de red profesional*