# Guía de Pruebas Anti-Sniffing para ProvesiWMS

## 🎯 Objetivo

Validar que la aplicación **previene ataques de sniffing** mediante encriptación de datos en tránsito, headers de seguridad y ocultación de información sensible.

## 🛡️ ¿Qué es el Sniffing?

**Sniffing** es una técnica donde un atacante intercepta y analiza el tráfico de red para:
- 🔍 **Capturar credenciales** enviadas en texto plano
- 📡 **Interceptar tokens** de autenticación 
- 🕵️ **Extraer información** sensible de las comunicaciones
- 📋 **Analizar patrones** de tráfico para obtener datos

## 📁 Archivo de Pruebas

### `Anti_Sniffing_Security_Tests.postman_collection.json`

**Categorías de Prueba:**

### 🔐 Test 1: Forzar HTTPS
- **Intento de login via HTTP** - Debe fallar o redirigir
- **Verificar redirección automática** a HTTPS
- **Validar que no se exponen** credenciales en HTTP

### 🛡️ Test 2: Headers de Seguridad
- **HSTS (HTTP Strict Transport Security)** - Previene downgrades
- **Secure Cookie Settings** - Cookies marcadas como seguras
- **X-Content-Type-Options** - Previene MIME type sniffing
- **X-Frame-Options** - Previene clickjacking
- **Content Security Policy** - Control de recursos

### 🔍 Test 3: Detección de Información Sensible
- **Headers del servidor** no deben revelar versiones específicas
- **Respuestas de error** no deben mostrar stack traces
- **Páginas 404** no deben revelar estructura interna

### 🕵️ Test 4: Protección de Datos en Tránsito
- **Encriptación de credenciales** via HTTPS/TLS
- **Protección de tokens JWT** durante transmisión
- **Verificar que tokens no aparecen** en logs o respuestas

### 🚫 Test 5: Prevención de Man-in-the-Middle
- **Certificate Pinning** (opcional pero recomendado)
- **Integridad de respuestas** via HTTPS
- **Validación de tokens JWT** no modificados

## 🔧 Herramientas Adicionales para Pruebas de Sniffing

### 1. Wireshark (Análisis de Tráfico)

```bash
# Instalar Wireshark (macOS)
brew install wireshark

# Capturar tráfico en interfaz de red
sudo wireshark
```

**Qué verificar en Wireshark:**
- ✅ Todo el tráfico hacia tu aplicación debe ser **HTTPS (TLS)**
- ❌ **NO debe haber** tráfico HTTP con credenciales
- ✅ Los **handshakes TLS** deben completarse correctamente
- ❌ **NO debe haber** datos de autenticación en texto plano

### 2. tcpdump (Captura de Paquetes)

```bash
# Capturar tráfico HTTPS hacia tu servidor
sudo tcpdump -i any -s 0 -w capture.pcap host tu-servidor.com and port 443

# Analizar la captura
tcpdump -r capture.pcap -A | grep -i "authorization\|password\|token"
```

**Resultado esperado:** NO debe encontrar credenciales en texto plano.

### 3. SSL Labs Test (Verificación de HTTPS)

```bash
# Probar la configuración SSL de tu servidor
curl -s "https://api.ssllabs.com/api/v3/analyze?host=tu-servidor.com" | jq
```

**O usar la web:** https://www.ssllabs.com/ssltest/

**Métricas importantes:**
- **Grade A o A+** en SSL Labs
- **TLS 1.2 o superior**
- **HSTS habilitado**
- **Perfect Forward Secrecy**

### 4. nmap (Escaneo de SSL/TLS)

```bash
# Verificar configuración SSL/TLS
nmap --script ssl-enum-ciphers -p 443 tu-servidor.com

# Verificar headers de seguridad
nmap --script http-security-headers -p 443 tu-servidor.com
```

### 5. OWASP ZAP (Proxy de Seguridad)

```bash
# Instalar OWASP ZAP
brew install --cask owasp-zap

# Usar como proxy para interceptar tráfico
# Configurar proxy en 127.0.0.1:8080
```

**Configuración para pruebas:**
1. Configurar ZAP como proxy en tu navegador
2. Navegar a tu aplicación
3. Verificar que **NO** se capturen credenciales en texto plano

## 📋 Checklist de Protección Anti-Sniffing

### ✅ Configuración de HTTPS
- [ ] Certificado SSL válido instalado
- [ ] Todo el tráfico forzado a HTTPS
- [ ] HTTP redirige automáticamente a HTTPS
- [ ] TLS 1.2 o superior habilitado

### ✅ Headers de Seguridad
- [ ] `Strict-Transport-Security` configurado
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY` o `SAMEORIGIN`
- [ ] Cookies marcadas como `Secure` y `HttpOnly`

### ✅ Ocultación de Información
- [ ] Server header no revela versiones específicas
- [ ] Errores no muestran stack traces
- [ ] No se expone información de debug
- [ ] Páginas 404 genéricas

### ✅ Protección de Credenciales
- [ ] Passwords nunca enviados en texto plano
- [ ] Tokens JWT transmitidos solo via HTTPS
- [ ] Credenciales no aparecen en logs
- [ ] Session cookies seguras

## 🔬 Pruebas Manuales Específicas

### Prueba 1: Interceptar con Burp Suite

```bash
# 1. Configurar Burp Suite como proxy
# 2. Hacer login en tu aplicación
# 3. Verificar en "HTTP history" de Burp
# 4. VERIFICAR: No debe haber requests HTTP con credenciales
```

### Prueba 2: Análisis de Certificado

```bash
# Verificar información del certificado SSL
openssl s_client -connect tu-servidor.com:443 -servername tu-servidor.com

# Verificar cadena de certificados
curl -I https://tu-servidor.com
```

### Prueba 3: Test de Downgrade Attack

```bash
# Intentar forzar HTTP (debe fallar)
curl -v http://tu-servidor.com/login

# Debe retornar 301/302 redirect a HTTPS
# O 403/404 si HTTP está deshabilitado completamente
```

## 🚨 Señales de Alerta (Vulnerabilidades)

### ❌ CRÍTICO - Fallas de Seguridad
- **Credenciales en HTTP:** Passwords visibles en texto plano
- **Tokens no protegidos:** JWT enviados via HTTP
- **Sin HSTS:** Posible downgrade a HTTP
- **Certificado inválido:** Warnings de SSL en navegador

### ⚠️ ADVERTENCIA - Mejoras Recomendadas
- **Headers faltantes:** CSP, X-Frame-Options ausentes
- **Información del servidor:** Versiones específicas expuestas
- **Cookies inseguras:** Sin flags Secure/HttpOnly
- **Cipher suites débiles:** TLS 1.0/1.1 habilitado

## 🛠️ Comandos de Verificación Rápida

```bash
# 1. Verificar HTTPS forzado
curl -I http://tu-servidor.com
# Debe retornar 301/302 redirect

# 2. Verificar headers de seguridad
curl -I https://tu-servidor.com
# Debe incluir HSTS, X-Content-Type-Options, etc.

# 3. Test de login HTTPS
curl -k -X POST https://tu-servidor.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
# Debe funcionar solo con HTTPS

# 4. Verificar información del servidor
curl -I https://tu-servidor.com | grep -i server
# No debe revelar versiones específicas
```

## 📊 Interpretación de Resultados

### ✅ Sistema Seguro Contra Sniffing
```
🔒 HTTPS: Forzado en todas las conexiones
🛡️  HSTS: Configurado con max-age adecuado
🚫 HTTP: Rechazado o redirigido automáticamente
🔐 Tokens: Transmitidos solo via HTTPS
🕵️ Información: Ocultada correctamente
```

### ❌ Sistema Vulnerable a Sniffing
```
⚠️  HTTP: Acepta conexiones inseguras
💥 Credenciales: Visibles en texto plano
🚨 Headers: Faltantes o mal configurados
📡 Información: Expuesta en respuestas
🔓 Tokens: Transmitidos sin protección
```

## 🎯 Resultado Esperado

Al ejecutar todas las pruebas, debes obtener:

1. **100% tráfico HTTPS** - Sin comunicación HTTP
2. **Headers de seguridad completos** - HSTS, X-Frame-Options, etc.
3. **Información sensible oculta** - Sin stack traces o versiones
4. **Tokens protegidos** - JWT solo via HTTPS
5. **Certificados válidos** - Sin warnings de SSL

Esto garantiza que **ningún atacante puede interceptar credenciales o datos sensibles** mediante sniffing de red.