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
