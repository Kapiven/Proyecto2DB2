# Documento del proyecto: Modelo de datos de detección de fraude

Este documento describe el modelo de datos implementado para el caso de uso de detección de fraude bancaria en Neo4j.

## Objetivo

El grafo modelado permite identificar comportamientos sospechosos en transacciones financieras mediante nodos, relaciones y propiedades que soportan análisis estructurado y reglas heurísticas.

## Entidades principales

### Cliente
Propiedades principales:
- `id`
- `nombre`
- `edad`
- `genero`
- `riesgo`
- `nivel_riesgo`
- `fecha_registro`
- `email`
- `telefono`

### Cuenta
Propiedades principales:
- `id`
- `saldo`
- `tipo`
- `estado`
- `fecha_apertura`
- `limite_credito`

### Tarjeta
Propiedades principales:
- `id`
- `numero`
- `tipo`
- `estado`
- `fecha_expiracion`
- `limite`

### Transaccion
Propiedades principales:
- `id`
- `monto`
- `fecha`
- `tipo`
- `fraudulenta`
- `estado`
- `canal`
- `razones_sospecha`

### Dispositivo
Propiedades principales:
- `id`
- `tipo`
- `ip_address`
- `user_agent`
- `ultima_conexion`

### Ubicacion
Propiedades principales:
- `id`
- `latitud`
- `longitud`
- `ciudad`
- `pais`
- `direccion`

### Comercio
Propiedades principales:
- `id`
- `nombre`
- `categoria`
- `riesgo`
- `ciudad`

### Banco
Propiedades principales:
- `id`
- `nombre`
- `codigo`
- `ciudad`
- `tipo`
- `riesgo`
- `nivel_riesgo`

### Alerta
Propiedades principales:
- `id`
- `tipo_alerta`
- `fecha`
- `severidad`
- `descripcion`
- `resuelta`

## Tipos de relaciones

- `TIENE_CUENTA` (Cliente -> Cuenta)
- `USA_DISPOSITIVO` (Cliente -> Dispositivo)
- `TIENE_TARJETA` (Cuenta -> Tarjeta)
- `ORIGINA` (Cuenta -> Transaccion)
- `DESTINADA_A` (Cuenta -> Transaccion)
- `UTILIZA_DISPOSITIVO` (Transaccion -> Dispositivo)
- `DESDE_UBICACION` (Transaccion -> Ubicacion)
- `EN_COMERCIO` (Transaccion -> Comercio)
- `UTILIZA_TARJETA` (Transaccion -> Tarjeta)
- `GENERA_ALERTA` (Transaccion -> Alerta)
- `PERTENECE_A` (Cuenta -> Banco)
- `LOCALIZADO_EN` (Dispositivo -> Ubicacion)

## Labels dinámicos

- `Cliente`: `AltoRiesgo`, `RiesgoMedio`, `RiesgoBajo`
- `Transaccion`: `Fraudulenta`, `Sospechosa`
- `Cuenta`: `Bloqueada`, `Sospechosa`
- `Comercio`: `AltoRiesgo`

## Comentarios sobre el diagrama

El diagrama base del grafo de fraude está disponible en el archivo `Cliente Risk Management.png`. Este documento describe el conjunto actual de nodos, relaciones y propiedades implementadas en el proyecto.

## Endpoint de datos principales

- `POST /api/generate/fake-data/` - Genera dataset sintético y conectado.
- `POST /api/upload/csv/` - Carga nodos y relaciones desde CSV.
- `GET /api/analytics/demo-queries/` - Ejecuta consultas de ejemplo.
- `POST /api/fraud/detect/` - Ejecuta reglas de detección automáticas.

## Nuevas operaciones en lote implementadas

- `POST /api/nodes/properties/batch/` - Asigna o actualiza propiedades en múltiples nodos.
- `DELETE /api/nodes/properties/batch/` - Elimina propiedades de múltiples nodos.
- `POST /api/nodes/delete/` - Elimina múltiples nodos.
- `POST /api/relationships/properties/batch/` - Asigna o actualiza propiedades en múltiples relaciones.
- `DELETE /api/relationships/properties/batch/` - Elimina propiedades de múltiples relaciones.
- `POST /api/relationships/delete/` - Elimina múltiples relaciones.

## Motor Heurístico de Detección de Fraude (Completamente Funcional)

El motor de fraude implementa 4 reglas heurísticas que se ejecutan automáticamente al llamar a `POST /api/fraud/detect/`.

### Reglas Implementadas

1. **Transacciones Rápidas (Burst)** - Detecta 2+ transacciones en una ventana de 10 minutos
2. **Cambios Sospechosos de Ubicación** - Identifica transacciones en países diferentes en menos de 30 minutos
3. **Dispositivos Compartidos** - Flagea cuando el mismo dispositivo es usado por múltiples clientes
4. **Comercios de Alto Riesgo** - Marca transacciones en comercios con riesgo >= 8

### Arquitectura

- **Servicio**: `backend/apps/graph/services/fraud_service.py` - Motor de detección
- **Vistas**: `backend/apps/graph/views/fraud_views.py` - Endpoint REST
- **Base de Datos**: Neo4j AuraDB con consultas Cypher optimizadas
- **Respuesta**: JSON estructurado legible para usuarios no técnicos

### Estructura de Respuesta Mejorada

La respuesta incluye:
- **Reporte**: Título, fecha, estado general (BAJO/MEDIO/ALTO), total de alertas
- **Resumen**: Explicación ejecutiva legible en español
- **Detalle de Reglas**: Para cada regla: casos detectados, definición técnica, explicación para no técnicos, nivel de riesgo
- **Recomendaciones**: Acciones sugeridas basadas en alertas
- **Próximos Pasos**: Flujo de escalación ordenado

### Ejemplo de Uso

```bash
curl -X POST http://127.0.0.1:8000/api/fraud/detect/
```

Respuesta esperada (con alertas):
```json
{
  "reporte": {
    "titulo": "REPORTE DE DETECCION DE FRAUDE",
    "fecha_analisis": "2026-05-02T19:06:39.828817",
    "estado_general": "MEDIO - Revisar",
    "total_alertas_detectadas": 2
  },
  "resumen": "⚠️ Se detectaron 1 transacción con dispositivo compartido...",
  "detalle_reglas": { ... },
  "recomendaciones": [ ... ],
  "proximos_pasos": [ ... ]
}
```

### Documentación Completa

Ver [FRAUD_ENGINE_RESPONSE.md](FRAUD_ENGINE_RESPONSE.md) para ejemplos detallados y guía de integración.
Ver [frontend/fraude_report_ejemplo.html](frontend/fraude_report_ejemplo.html) para visualización de ejemplo en HTML.
