# CHECKLIST WIRESHARK - VALIDACIÓN ANTI-SNIFFING
# Fecha: _______________
# Analista: _______________
# Target: provesi-alb-2003818714.us-east-1.elb.amazonaws.com

## 1. REDIRECCIÓN HTTPS FORZADA
□ Filtro aplicado: `http and host provesi-alb-2003818714.us-east-1.elb.amazonaws.com`
□ Resultado: Solo códigos 301/302 con Location: https://
□ ❌ FALLO si: Respuestas 200 con contenido en HTTP
□ Notas: ________________________________

## 2. HANDSHAKE TLS SEGURO
□ Filtro aplicado: `tls.handshake.type == 1`
□ Versión TLS detectada: TLS 1.__ (debe ser 1.2 o 1.3)
□ Cipher Suite contiene: ECDHE-______________
□ Perfect Forward Secrecy: □ SÍ □ NO
□ Certificado: □ Válido □ Auto-firmado □ Expirado
□ ❌ FALLO si: TLS < 1.2, sin ECDHE, certificado inválido
□ Notas: ________________________________

## 3. BÚSQUEDA DE TEXTO PLANO
□ Filtro aplicado: `tcp contains "password"`
□ Resultados encontrados: _____ paquetes
□ Filtro aplicado: `tcp contains "admin"`  
□ Resultados encontrados: _____ paquetes
□ Filtro aplicado: `tcp contains "secret"`
□ Resultados encontrados: _____ paquetes
□ ❌ CRÍTICO si: Cualquier resultado > 0
□ Notas: ________________________________

## 4. ANÁLISIS SSL STREAM
□ Follow SSL Stream ejecutado: □ SÍ □ NO
□ Datos visibles en texto plano: □ SÍ □ NO
□ Solo datos cifrados observados: □ SÍ □ NO
□ ❌ CRÍTICO si: Datos en texto plano visibles
□ Notas: ________________________________

## 5. PROTOCOLOS INSEGUROS
□ Filtro aplicado: `ssl`
□ TLS 1.0 detectado: □ SÍ □ NO
□ TLS 1.1 detectado: □ SÍ □ NO
□ SSLv3 detectado: □ SÍ □ NO
□ ❌ FALLO si: Cualquier protocolo inseguro detectado
□ Notas: ________________________________

## 6. CIPHER SUITES DÉBILES
□ RC4 detectado: □ SÍ □ NO
□ DES/3DES detectado: □ SÍ □ NO
□ MD5 hash detectado: □ SÍ □ NO
□ NULL cipher detectado: □ SÍ □ NO
□ ❌ CRÍTICO si: Cualquier cipher débil detectado
□ Notas: ________________________________

## 7. TIMING ANALYSIS
□ Conexiones establecidas: _____ total
□ Tiempo promedio handshake: _____ ms
□ Anomalías de timing: □ SÍ □ NO
□ Notas: ________________________________

## RESULTADO FINAL
□ ✅ SISTEMA SEGURO - No se puede realizar sniffing exitoso
□ ⚠️ VULNERABILIDADES MENORES - Requiere mejoras
□ ❌ SISTEMA VULNERABLE - Sniffing es posible

## CONCLUSIÓN REQUISITO
"El atacante no pueda ver la informacion en texto plano"
□ ✅ REQUISITO CUMPLIDO
□ ❌ REQUISITO NO CUMPLIDO

## EVIDENCIA ADJUNTA
□ Captura .pcap guardada
□ Screenshots de vulnerabilidades
□ Logs de análisis SSL
□ Reporte exportado

Firma: _______________
Fecha: _______________