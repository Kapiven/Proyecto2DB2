"""Definición del esquema de negocio y consultas demo."""

NODE_SCHEMAS = {
    "Cliente": ["id", "nombre", "edad", "genero", "riesgo", "nivel_riesgo", "fecha_registro", "email", "telefono"],
    "Cuenta": ["id", "saldo", "tipo", "estado", "fecha_apertura", "limite_credito"],
    "Tarjeta": ["id", "numero", "tipo", "estado", "fecha_expiracion", "limite"],
    "Transaccion": ["id", "monto", "fecha", "tipo", "fraudulenta", "estado", "canal", "razones_sospecha"],
    "Dispositivo": ["id", "tipo", "ip_address", "user_agent", "ultima_conexion"],
    "Ubicacion": ["id", "latitud", "longitud", "ciudad", "pais", "direccion"],
    "Comercio": ["id", "nombre", "categoria", "riesgo", "ciudad"],
    "Banco": ["id", "nombre", "codigo", "ciudad", "tipo", "riesgo", "nivel_riesgo"],
    "Alerta": ["id", "tipo_alerta", "fecha", "severidad", "descripcion", "resuelta"],
}

RELATIONSHIP_SCHEMAS = {
    "TIENE_CUENTA": ["fecha_asignacion", "tipo_relacion", "es_principal"],
    "USA_DISPOSITIVO": ["fecha_uso", "primera_vez", "veces_usado"],
    "TIENE_TARJETA": ["fecha_emision", "es_principal", "estado_asignacion"],
    "ORIGINA": ["fecha_origen", "tipo_operacion", "es_inusual"],
    "DESTINADA_A": ["fecha_destino", "tipo_destino", "es_sospechosa"],
    "UTILIZA_DISPOSITIVO": ["fecha", "dispositivo_nuevo", "coincidencia_usuario"],
    "DESDE_UBICACION": ["distancia_km", "es_anomala", "cambio_pais"],
    "EN_COMERCIO": ["frecuencia_cliente", "es_comercio_habitual", "coincidencia_categoria"],
    "UTILIZA_TARJETA": ["metodo_autenticacion", "intento_fallido", "tarjeta_nueva"],
    "GENERA_ALERTA": ["score_riesgo", "regla_activada", "prioridad"],
    "PERTENECE_A": ["fecha_asociacion", "canal_apertura", "verificada"],
    "LOCALIZADO_EN": ["fecha", "tipo_conexion", "ip_detectada"],
    "REMITE": ["monto_recibido", "fecha_recepcion", "comision"],
    "INTERACTUA": ["tipo_transferencia", "codigo_swift", "costo_transferencia", "tiempo_procesamiento"],
}

DYNAMIC_LABELS = {
    "Cliente": ["AltoRiesgo", "RiesgoMedio", "RiesgoBajo"],
    "Transaccion": ["Fraudulenta", "Sospechosa"],
    "Cuenta": ["Bloqueada", "Sospechosa"],
    "Comercio": ["AltoRiesgo"],
}

DEMO_QUERIES = [
    {
        "name": "Clientes con más alertas",
        "cypher": """
            MATCH (c:Cliente)-[:TIENE_CUENTA]->(:Cuenta)-[:ORIGINA]->(:Transaccion)-[:GENERA_ALERTA]->(a:Alerta)
            RETURN c.id AS cliente_id, c.nombre AS cliente, count(a) AS total_alertas
            ORDER BY total_alertas DESC LIMIT 10
        """,
    },
    {
        "name": "Comercios de alto riesgo con mayor volumen",
        "cypher": """
            MATCH (:Transaccion)-[:EN_COMERCIO]->(m:Comercio)
            WHERE m.riesgo >= 7 OR m:AltoRiesgo
            RETURN m.nombre AS comercio, m.categoria AS categoria, count(*) AS transacciones
            ORDER BY transacciones DESC LIMIT 10
        """,
    },
    {
        "name": "Dispositivos compartidos por múltiples clientes",
        "cypher": """
            MATCH (c:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)
            WITH d, count(DISTINCT c.id) AS clientes
            WHERE clientes > 1
            RETURN d.id AS dispositivo, clientes
            ORDER BY clientes DESC
        """,
    },
    {
        "name": "Transacciones sospechosas por cambio de ubicación",
        "cypher": """
            MATCH (t:Transaccion)-[r:DESDE_UBICACION]->(u:Ubicacion)
            WHERE r.es_anomala = true OR r.cambio_pais = true
            RETURN t.id AS transaccion, t.monto AS monto, u.ciudad AS ciudad, u.pais AS pais
            ORDER BY t.fecha DESC LIMIT 25
        """,
    },
    {
        "name": "Bancos con más cuentas asociadas",
        "cypher": """
            MATCH (:Cuenta)-[:PERTENECE_A]->(b:Banco)
            RETURN b.nombre AS banco, count(*) AS cuentas
            ORDER BY cuentas DESC
        """,
    },
    {
        "name": "Promedio de monto por canal",
        "cypher": """
            MATCH (t:Transaccion)
            RETURN t.canal AS canal, avg(t.monto) AS monto_promedio, count(*) AS total
            ORDER BY monto_promedio DESC
        """,
    },
]
