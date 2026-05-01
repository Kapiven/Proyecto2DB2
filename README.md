# Sistema de detección de fraude con Neo4j, Django y Vue

Proyecto full-stack separado en dos carpetas:

- `backend/`: API REST con Django + Django REST Framework.
- `frontend/`: cliente Vue que consume la API.

La solución fue diseñada para cumplir la rúbrica solicitada:

- grafo con 9 etiquetas de nodos;
- 12 tipos de relaciones;
- propiedades ricas en nodos y relaciones;
- CRUD de nodos, relaciones y propiedades;
- carga por CSV;
- generación de más de 5000 nodos falsos;
- consultas Cypher, agregaciones y filtros;
- soporte de labels dinámicos;
- algoritmos GDS con fallback cuando no estén disponibles.

## Arquitectura

### Backend

El backend sigue una separación por capas:

- `views/`: recibe HTTP y valida entrada.
- `serializers/`: valida payloads con DRF.
- `services/`: concentra la lógica de negocio y las consultas Cypher.
- `utils/schema.py`: documenta el esquema del dominio.

No se usan modelos relacionales para el negocio porque la persistencia real está en Neo4j AuraDB mediante el driver oficial `neo4j`.

### Frontend

El frontend está separado y usa:

- `Vue 3`
- `Vue Router`
- `Axios`
- SVG simple para visualización de grafo

## Modelo del grafo

### Nodos incluidos

- `Cliente`
- `Cuenta`
- `Tarjeta`
- `Transaccion`
- `Dispositivo`
- `Ubicacion`
- `Comercio`
- `Banco`
- `Alerta`

### Relaciones incluidas

- `TIENE_CUENTA`
- `USA_DISPOSITIVO`
- `TIENE_TARJETA`
- `ORIGINA`
- `DESTINADA_A`
- `UTILIZA_DISPOSITIVO`
- `DESDE_UBICACION`
- `EN_COMERCIO`
- `UTILIZA_TARJETA`
- `GENERA_ALERTA`
- `PERTENECE_A`
- `LOCALIZADO_EN`

### Labels múltiples soportados

- `Cliente:AltoRiesgo`
- `Cliente:RiesgoMedio`
- `Cliente:RiesgoBajo`
- `Transaccion:Fraudulenta`
- `Transaccion:Sospechosa`
- `Cuenta:Bloqueada`
- `Cuenta:Sospechosa`
- `Comercio:AltoRiesgo`

## Tipos de datos soportados

La API y la carga CSV contemplan:

- `String`
- `Integer`
- `Float`
- `Boolean`
- `List`
- `Date`
- `DateTime`

## Requisitos previos

- Python 3.11+
- Node.js 20+
- cuenta de `Neo4j AuraDB`

## Configuración del backend

### 1. Instalar dependencias

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copiar `backend/.env.example` a `backend/.env` y completar credenciales de AuraDB.

Variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

> Si usas AuraDB, copia el usuario, URI y contraseña exactos que aparecen en el panel de la base de datos. Una contraseña antigua o incorrecta causará `Neo4j authentication failed`.

### 3. Ejecutar backend

```powershell
cd backend
python manage.py migrate
python manage.py runserver
```

API base:

- `http://127.0.0.1:8000/api/`

> Documento del modelo de datos disponible en `DOCUMENTO_DE_PROYECTO.md`.

## Configuración del frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend base:

- `http://127.0.0.1:5173`

## Flujo recomendado de demostración

1. Inicializar índices con `POST /api/schema/bootstrap/`.
2. Generar dataset sintético con `POST /api/generate/fake-data/`.
3. Revisar `GET /api/dashboard/`.
4. Ejecutar `POST /api/fraud/detect/`.
5. Probar `POST /api/gds/run/`.
6. Visualizar el grafo desde el frontend.

## Endpoints principales

### Dashboard y analítica

- `GET /api/dashboard/`
- `GET /api/analytics/aggregations/`
- `GET /api/analytics/demo-queries/`
- `GET /api/analytics/graph-snapshot/`

### Nodos

- `GET /api/nodes/?label=Cliente`
- `POST /api/nodes/`
- `GET /api/nodes/<label>/<node_id>/`
- `PUT /api/nodes/<label>/<node_id>/`
- `DELETE /api/nodes/<label>/<node_id>/`
- `PUT /api/nodes/<label>/<node_id>/properties/<property_name>/`
- `DELETE /api/nodes/<label>/<node_id>/properties/<property_name>/`
- `POST /api/nodes/properties/batch/`
- `DELETE /api/nodes/properties/batch/`
- `POST /api/nodes/delete/`
- `POST /api/nodes/<label>/<node_id>/labels/`

### Relaciones

- `GET /api/relationships/`
- `POST /api/relationships/`
- `GET /api/relationships/<relationship_id>/`
- `PUT /api/relationships/<relationship_id>/`
- `DELETE /api/relationships/<relationship_id>/`
- `PUT /api/relationships/<relationship_id>/properties/<property_name>/`
- `DELETE /api/relationships/<relationship_id>/properties/<property_name>/`
- `POST /api/relationships/properties/batch/`
- `DELETE /api/relationships/properties/batch/`
- `POST /api/relationships/delete/`

### Ingesta

- `POST /api/upload/csv/`
- `POST /api/generate/fake-data/`
- `POST /api/schema/bootstrap/`

### Fraude

- `GET /api/fraud/rules/`
- `POST /api/fraud/detect/`

### GDS

- `POST /api/gds/run/`

Payload ejemplo:

```json
{
  "algorithm": "pagerank"
}
```

Para shortest path:

```json
{
  "algorithm": "shortest_path",
  "source_id": "CLI-00001",
  "target_id": "COM-0001"
}
```

## Carga CSV

La API acepta entidades de nodos y relaciones. Archivos de ejemplo incluidos en `samples/`.

Ejemplo para nodos:

```csv
id,nombre,edad,genero,riesgo,nivel_riesgo,fecha_registro,email,telefono
CLI-CSV-001,Ana López,31,F,0.31,Bajo,2025-02-10,ana@example.com,5555-1111
```

Ejemplo para relaciones:

```csv
start_id,end_id,fecha_asignacion,tipo_relacion,es_principal
CLI-CSV-001,CUE-CSV-001,2024-01-10,Titular,true
```

## Generación de más de 5000 nodos

El endpoint `POST /api/generate/fake-data/` crea un grafo conectado.

Payload recomendado:

```json
{
  "total_clientes": 1000,
  "cuentas_por_cliente": 1,
  "transacciones_por_cuenta": 4
}
```

Con esa configuración se supera ampliamente el mínimo de 5000 nodos porque además se crean cuentas, tarjetas, dispositivos, transacciones, alertas, bancos, comercios y ubicaciones.

## Lógica de fraude automática

Se implementaron reglas heurísticas:

- múltiples transacciones en corto tiempo;
- cambios de ubicación en ventana corta;
- dispositivos compartidos entre clientes;
- comercios de alto riesgo.

Estas reglas:

- asignan labels como `Sospechosa` o `Fraudulenta`;
- actualizan banderas de fraude;
- crean alertas automáticas cuando corresponde.

## GDS y fallback

Se intentan ejecutar:

- `PageRank`
- `Louvain`
- `Node Similarity`
- `Shortest Path`

Si Neo4j AuraDB no tiene GDS habilitado o una proyección falla, la API responde usando consultas fallback basadas en Cypher estándar.

## Seis consultas Cypher incluidas

Las consultas demo cubren:

1. clientes con más alertas;
2. comercios de alto riesgo con mayor volumen;
3. dispositivos compartidos por múltiples clientes;
4. transacciones sospechosas por ubicación;
5. bancos con más cuentas asociadas;
6. promedio de monto por canal.

Se exponen en `GET /api/analytics/demo-queries/`.

## Observaciones importantes

- El proyecto está comentado en español para facilitar su defensa.
- Se recomienda ejecutar primero la generación sintética y luego la detección de fraude.
- Algunas consultas usan GDS cuando existe; cuando no, se activa fallback.
