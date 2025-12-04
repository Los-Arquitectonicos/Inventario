# Análisis de Seguridad - ProvesiWMS con Kong

## Arquitectura Actual

```
Internet (HTTP) → Kong:8000 → ALB:443 (HTTPS) → Django:8080
                              └→ Notifications:8001 (HTTP)
```

## Estado de Seguridad por Segmento

### 1. Internet → Kong (⚠️ HTTP sin cifrar)
**Estado**: NO SEGURO
- Protocolo: HTTP (puerto 8000)
- Cifrado: Ninguno
- **Riesgo**: El tráfico entre el cliente y Kong viaja en texto plano
- **Datos expuestos**: Credenciales, tokens JWT, datos de negocio

**Solución recomendada**:
```yaml
# Agregar listener HTTPS en Kong
# Crear certificado para Kong y exponer puerto 8443
```

### 2. Kong → ALB (✅ HTTPS cifrado)
**Estado**: SEGURO
- Protocolo: HTTPS (puerto 443)
- Certificado: Self-signed (válido para cifrado, no para validación)
- Configuración Kong: `tls_verify: false`
- **Cifrado**: Activo (TLS 1.2+)
- **Datos protegidos**: Todo el tráfico está cifrado

**Nota sobre `tls_verify: false`**:
- ✅ El tráfico SÍ está cifrado (HTTPS funciona)
- ❌ Kong NO valida la identidad del certificado (acepta cualquier certificado)
- ⚠️ Vulnerable a ataques MITM en la red interna AWS (riesgo bajo)

### 3. ALB → Django (⚠️ HTTP sin cifrar)
**Estado**: NO SEGURO dentro de la VPC
- Protocolo: HTTP (puerto 8080)
- Cifrado: Ninguno
- Red: VPC privada de AWS
- **Riesgo**: Bajo (tráfico interno en AWS)
- **Datos expuestos**: Visibles dentro de la VPC

### 4. Kong → Notifications (⚠️ HTTP sin cifrar)
**Estado**: NO SEGURO dentro de la VPC
- Protocolo: HTTP (puerto 8001)
- Cifrado: Ninguno
- Red: VPC privada de AWS
- **Riesgo**: Bajo (tráfico interno)

## Configuración de Seguridad Django

```python
# settings.py - Configuración actual
SECURE_SSL_REDIRECT = not DEBUG  # ✅ Fuerza HTTPS en producción
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # ✅ Detecta HTTPS del ALB
SESSION_COOKIE_SECURE = not DEBUG  # ✅ Cookies solo por HTTPS
CSRF_COOKIE_SECURE = not DEBUG  # ✅ CSRF cookies solo por HTTPS
```

## Certificado SSL Actual

**Tipo**: Self-signed (generado por Terraform)
**Características**:
- ✅ Proporciona cifrado TLS completo
- ❌ No es confiable para navegadores (muestra advertencia)
- ❌ No valida identidad del servidor
- ⏱️ Válido por 1 año

**Para producción, usar**:
- AWS Certificate Manager (ACM) con dominio real
- Let's Encrypt con dominio público
- Certificado corporativo de CA reconocida

## Recomendaciones de Seguridad

### Críticas (Implementar de inmediato)
1. **Agregar HTTPS en Kong**
   ```bash
   # Exponer Kong en puerto 8443 con certificado SSL
   # Redirigir puerto 8000 → 8443
   ```

2. **Usar certificado válido en ALB**
   ```hcl
   # Opción A: ACM con dominio
   resource "aws_acm_certificate" "alb" {
     domain_name       = "api.provesi.com"
     validation_method = "DNS"
   }
   
   # Opción B: Importar certificado corporativo
   ```

### Importantes (Corto plazo)
3. **Habilitar verificación de certificados Kong → ALB**
   - Requiere certificado válido en ALB primero
   - Cambiar `tls_verify: false` a `tls_verify: true`

4. **Cifrar tráfico interno ALB → Django**
   - Configurar Django para HTTPS en puerto 8443
   - Actualizar Target Group del ALB

### Opcionales (Mejora continua)
5. **Implementar mTLS entre Kong y ALB**
   - Autenticación mutua con certificados de cliente
   
6. **VPC Endpoints para servicios AWS**
   - Eliminar tráfico público para accesos a AWS

7. **AWS WAF en el ALB**
   - Protección contra OWASP Top 10
   - Rate limiting
   - Geo-blocking

## Resumen de Riesgos

| Segmento | Protocolo | Cifrado | Riesgo | Prioridad |
|----------|-----------|---------|--------|-----------|
| Internet → Kong | HTTP | ❌ No | 🔴 ALTO | CRÍTICA |
| Kong → ALB | HTTPS | ✅ Sí (sin validar) | 🟡 MEDIO | ALTA |
| ALB → Django | HTTP | ❌ No | 🟢 BAJO | MEDIA |
| Kong → Notifications | HTTP | ❌ No | 🟢 BAJO | MEDIA |

## Estado Actual vs Producción

### Entorno Actual (Desarrollo/Testing)
✅ Adecuado para pruebas internas
✅ Cifrado Kong → ALB funcional
⚠️ No apto para exposición pública sin HTTPS en Kong

### Requisitos para Producción
- [ ] HTTPS en Kong (puerto 8443)
- [ ] Certificado ACM o válido en ALB
- [ ] Habilitar `tls_verify: true` en Kong
- [ ] Considerar cifrado interno (ALB → Django)
- [ ] Implementar AWS WAF
- [ ] Configurar logs de auditoría

## Comandos de Verificación

```bash
# Verificar conexión HTTPS del ALB
openssl s_client -connect provesi-alb-272371447.us-east-1.elb.amazonaws.com:443 -showcerts

# Verificar headers de seguridad
curl -I https://provesi-alb-272371447.us-east-1.elb.amazonaws.com/inventario/

# Test de cifrado Kong → ALB
# (Desde dentro de la instancia Kong)
curl -v https://provesi-alb-272371447.us-east-1.elb.amazonaws.com/inventario/
```

## Conclusión

**La conexión Kong → ALB SÍ está cifrada**, pero:
- ⚠️ Kong no valida el certificado (`tls_verify: false`)
- ⚠️ El tráfico Internet → Kong NO está cifrado
- ✅ Para producción, se necesita HTTPS en Kong y certificado válido en ALB

**Nivel de seguridad actual**: Apropiado para desarrollo/testing interno, **NO para producción pública**.
