# Plan: Microservicios Sencillos para ProvesiWMS (Actualizado con Serverless)

Basándome en el análisis del codebase de ProvesiWMS, propongo tres microservicios simples que agregan valor inmediato al negocio. El **Servicio de Analytics/Reportes** implementará un patrón serverless con AWS Lambda por sus características ideales para esta arquitectura.

## Microservicios Propuestos

### 1. **Servicio de Notificaciones**
Extrae la funcionalidad de alertas y comunicaciones del sistema principal.

**Funcionalidad:**
- Notificaciones de stock bajo
- Alertas de estado de pedidos  
- Comunicación con clientes vía email/SMS
- Dashboard de notificaciones para administrativos

**Base de datos:** Amazon DynamoDB para logs de notificaciones y preferencias de usuario

### 2. **Servicio de Analytics/Reportes (Serverless)** ⚡
Servicio completamente serverless para generación de reportes y métricas de negocio.

**Funcionalidad:**
- Generación de reportes on-demand (ventas, inventario, KPIs)
- Agregación de métricas históricas 
- Dashboards ejecutivos con datos calculados
- Análisis de tendencias y forecasting básico

**Arquitectura Serverless:**
- **AWS Lambda**: Para procesamiento de reportes bajo demanda
- **Amazon DocumentDB**: Para almacenar datos agregados y métricas históricas
- **API Gateway**: Como punto de entrada REST
- **EventBridge**: Para triggers automáticos de reportes

**Base de datos:** Amazon DocumentDB (MongoDB compatible) para almacenar datos agregados

### 3. **Servicio de Workflow de Pedidos**
Microservicio independiente para orquestación del ciclo de vida completo de pedidos.

**Funcionalidad:**
- Gestión de estados: Alistamiento → Empaque → Verificación → Envío
- Asignación de tareas a empleados por etapa
- Métricas de tiempo y productividad por etapa
- Dashboard operativo para supervisores
- API de eventos para notificar cambios de estado

**Arquitectura:**
- **Aplicación**: Node.js/Express o Python/FastAPI (independiente del monolito Django)
- **Comunicación**: REST API + EventBridge para integración asíncrona
- **Deployment**: ECS Fargate o Lambda (según preferencia de arquitectura)

**Base de datos:** Amazon DynamoDB para workflow events, task assignments y métricas de tiempo

## Razones para Serverless en Analytics/Reportes

1. **Workload Pattern**: Los reportes son esporádicos, no continuos - perfecto para Lambda's pay-per-use
2. **Processing Requirements**: Cálculos batch que se ejecutan y terminan - ideal para 15min timeout de Lambda  
3. **Scaling**: Los reportes requieren burst capacity ocasional, no carga constante
4. **Cost Optimization**: Solo se paga cuando se generan reportes, no por infraestructura idle
5. **Integration**: Fácil integración con DocumentDB y existing APIs via EventBridge

## Ventajas del Servicio de Workflow

1. **Modelos ya definidos**: `AlistamientoPedido`, `EmpaquePedido`, `VerificacionPedido`, `GuiaEnvioPedido` existen pero no se usan actualmente
2. **Bajo riesgo**: No modifica datos críticos de inventario, solo gestiona workflow operativo
3. **Valor inmediato**: Digitaliza proceso que probablemente se hace de forma manual
4. **KPIs operativos**: Genera métricas de productividad y tiempos por etapa
5. **Integración natural**: Se conecta con Notificaciones (#1) y Analytics (#2) vía eventos

## Pasos de Implementación

1. **Configurar infraestructura AWS** - Actualizar `terraform/main.tf` para Lambda, API Gateway, EventBridge, DocumentDB y DynamoDB
2. **Extraer lógica de reportes** - Migrar endpoints como `api_estadisticas_completas` y `reporte_ventas` a funciones Lambda  
3. **Implementar triggers automáticos** - EventBridge para reportes programados, notificaciones y eventos de workflow
4. **Crear agregaciones** - Pre-calcular métricas en DocumentDB usando datos de ProvesiWMS APIs
5. **Activar modelos de workflow** - Implementar lógica para `AlistamientoPedido`, `EmpaquePedido`, `VerificacionPedido`, `GuiaEnvioPedido`
6. **Configurar comunicación entre servicios** - REST APIs y EventBridge para integración asíncrona
7. **Testing y deployment** - Reutilizar patrones de `tests/escalabilidad` para validación

## Consideraciones Adicionales

1. **¿Reportes síncronos o asíncronos?** - Lambda async para reportes pesados vs API Gateway síncrono para dashboards
2. **¿Frecuencia de agregación?** - EventBridge scheduled para métricas diarias vs real-time para KPIs críticos
3. **¿Nivel de granularidad en datos históricos?** - Agregaciones por día/semana/mes vs datos transaccionales completos
4. **¿Tecnología para Workflow Service?** - Node.js/Express (rápido) vs Python/FastAPI (consistencia con Django) vs Lambda serverless
5. **¿Comunicación síncrona o asíncrona?** - REST directo para operaciones críticas vs EventBridge para eventos no bloqueantes
6. **¿Nivel de automatización en workflow?** - Asignación manual de tareas vs asignación automática por disponibilidad de empleados
