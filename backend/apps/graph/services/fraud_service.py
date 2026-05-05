"""Reglas de deteccion de fraude con evidencia estructurada."""

from .neo4j_service import Neo4jRepository



class FraudDetectionService:
    """Aplica heuristicas y devuelve IDs, evidencia y consultas auditables."""

    REQUIRED_LABELS = {"Cliente", "Cuenta", "Transaccion", "Dispositivo", "Ubicacion", "Comercio", "Alerta"}
    REQUIRED_RELATIONSHIPS = {
        "TIENE_CUENTA",
        "USA_DISPOSITIVO",
        "ORIGINA",
        "UTILIZA_DISPOSITIVO",
        "DESDE_UBICACION",
        "EN_COMERCIO",
        "GENERA_ALERTA",
    }

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def available_rules(self):
        return [
            {
                "rule": "rapid_transactions",
                "name": "Transacciones rapidas",
                "description": "Multiples movimientos de una misma cuenta dentro de 10 minutos.",
            },
            {
                "rule": "suspicious_locations",
                "name": "Ubicaciones sospechosas",
                "description": "Transacciones con ubicacion anomala o cambio de pais.",
            },
            {
                "rule": "shared_devices",
                "name": "Dispositivos compartidos",
                "description": "Un mismo dispositivo usado por varios clientes.",
            },
            {
                "rule": "high_risk_commerce",
                "name": "Comercio de alto riesgo",
                "description": "Transacciones en comercios marcados con riesgo=true o etiqueta AltoRiesgo.",
            },
            {
                "rule": "suspicious_labels",
                "name": "Transacciones etiquetadas",
                "description": "Transacciones ya marcadas como sospechosas, fraudulentas o con razones de sospecha.",
            },
        ]

    def schema_status(self) -> dict:
        labels = self.repository.execute_read("CALL db.labels() YIELD label RETURN collect(label) AS labels")
        rels = self.repository.execute_read(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationshipTypes"
        )
        current_labels = set(labels[0].get("labels", [])) if labels else set()
        current_rels = set(rels[0].get("relationshipTypes", [])) if rels else set()
        return {
            "labels": sorted(current_labels),
            "relationshipTypes": sorted(current_rels),
            "missingLabels": sorted(self.REQUIRED_LABELS - current_labels),
            "missingRelationshipTypes": sorted(self.REQUIRED_RELATIONSHIPS - current_rels),
            "removedLegacyLabels": sorted(current_labels & {"Actor", "Movie", "Person", "Film"}),
        }

    def detect(self):
        schema = self.schema_status()
        self._flag_rapid_transactions()
        self._flag_location_jumps()
        self._flag_shared_devices()
        self._flag_high_risk_commerce()

        rule_builders = [
            ("rapid_transactions", "Transacciones rapidas", self._rapid_transactions_results),
            ("suspicious_locations", "Ubicaciones sospechosas", self._suspicious_locations_results),
            ("shared_devices", "Dispositivos compartidos", self._shared_devices_results),
            ("high_risk_commerce", "Comercios de alto riesgo", self._high_risk_commerce_results),
            ("suspicious_labels", "Transacciones con etiquetas sospechosas", self._suspicious_label_results),
        ]
        rules = []
        for rule_id, title, builder in rule_builders:
            payload = builder()
            rules.append(
                {
                    "rule": rule_id,
                    "title": title,
                    "count": payload["count"],
                    "results": payload["results"],
                    "cypher": payload["cypher"],
                }
            )

        total_alerts = sum(rule["count"] for rule in rules)
        high_signal_rules = [rule["rule"] for rule in rules if rule["count"] > 0]
        return {
            "summary": {
                "total_alerts": total_alerts,
                "rules_triggered": len(high_signal_rules),
                "risk_level": self._risk_level(total_alerts),
                "schema_checked": True,
                "schema": schema,
            },
            "rules": rules,
        }

    def _risk_level(self, total: int) -> str:
        if total >= 80:
            return "alto"
        if total >= 20:
            return "medio"
        return "bajo"

    def _count(self, query: str) -> int:
        result = self.repository.execute_read(query)
        return int(result[0].get("count", 0)) if result else 0

    def _flag_rapid_transactions(self):
        query = """
            MATCH (c:Cuenta)-[:ORIGINA]->(t1:Transaccion),
                  (c)-[:ORIGINA]->(t2:Transaccion)
            WHERE t1.id <> t2.id
              AND datetime(t2.fecha) > datetime(t1.fecha)
              AND datetime(t2.fecha) <= datetime(t1.fecha) + duration({minutes: 10})
            SET t1:Sospechosa, t2:Sospechosa,
                t1.fraudulenta = coalesce(t1.fraudulenta, false),
                t2.fraudulenta = coalesce(t2.fraudulenta, false)
            RETURN count(DISTINCT t1) + count(DISTINCT t2) AS total
        """
        return self.repository.execute_write(query)

    def _flag_location_jumps(self):
        query = """
            MATCH (t:Transaccion)-[r:DESDE_UBICACION]->(:Ubicacion)
            WHERE r.es_anomala = true OR r.cambio_pais = true
            SET t:Sospechosa
            RETURN count(DISTINCT t) AS total
        """
        return self.repository.execute_write(query)

    def _flag_shared_devices(self):
        query = """
            MATCH (c1:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(c2:Cliente)
            WHERE c1.id <> c2.id
            MATCH (t:Transaccion)-[:UTILIZA_DISPOSITIVO]->(d)
            SET t:Sospechosa
            RETURN count(DISTINCT t) AS total
        """
        return self.repository.execute_write(query)

    def _flag_high_risk_commerce(self):
        query = """
            MATCH (t:Transaccion)-[:EN_COMERCIO]->(m:Comercio)
            WHERE m.riesgo = true OR m:AltoRiesgo
            SET t:Sospechosa
            WITH DISTINCT t, m
            MERGE (a:Alerta {id: 'AUTO-COMERCIO-' + t.id})
            SET a.tipo_alerta = 'Comercio de alto riesgo',
                a.fecha = datetime(),
                a.severidad = 'Alta',
                a.descripcion = 'Transaccion en comercio marcado como alto riesgo',
                a.resuelta = false
            MERGE (t)-[r:GENERA_ALERTA]->(a)
            SET r.score_riesgo = 0.92,
                r.regla_activada = 'comercio_alto_riesgo',
                r.prioridad = 'Alta'
            RETURN count(DISTINCT t) AS total
        """
        return self.repository.execute_write(query)

    def _rapid_transactions_results(self):
        cypher = """
            MATCH (cu:Cuenta)-[:ORIGINA]->(t1:Transaccion),
                  (cu)-[:ORIGINA]->(t2:Transaccion)
            WHERE t1.id <> t2.id
              AND datetime(t2.fecha) > datetime(t1.fecha)
              AND datetime(t2.fecha) <= datetime(t1.fecha) + duration({minutes: 10})
            WITH cu, t1, t2
            ORDER BY cu.id, t1.fecha
            RETURN cu.id AS cuenta_id,
                   collect(DISTINCT t1.id) + collect(DISTINCT t2.id) AS transacciones,
                   min(t1.fecha) AS inicio,
                   max(t2.fecha) AS fin,
                   count(DISTINCT t1) + count(DISTINCT t2) AS total_transacciones
            LIMIT 25
        """
        count_query = """
            MATCH (cu:Cuenta)-[:ORIGINA]->(t1:Transaccion),
                  (cu)-[:ORIGINA]->(t2:Transaccion)
            WHERE t1.id <> t2.id
              AND datetime(t2.fecha) > datetime(t1.fecha)
              AND datetime(t2.fecha) <= datetime(t1.fecha) + duration({minutes: 10})
            RETURN count(DISTINCT t1) + count(DISTINCT t2) AS count
        """
        return {"count": self._count(count_query), "results": self.repository.execute_read(cypher), "cypher": cypher.strip()}

    def _shared_devices_results(self):
        cypher = """
            MATCH (c:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(other:Cliente)
            WHERE c.id <> other.id
            WITH d, collect(DISTINCT c.id) + collect(DISTINCT other.id) AS raw_clientes
            UNWIND raw_clientes AS cliente_id
            WITH d, collect(DISTINCT cliente_id) AS clientes
            RETURN d.id AS dispositivo_id,
                   clientes,
                   size(clientes) AS total_clientes
            ORDER BY total_clientes DESC
            LIMIT 25
        """
        count_query = """
            MATCH (c:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(other:Cliente)
            WHERE c.id <> other.id
            RETURN count(DISTINCT d) AS count
        """
        return {"count": self._count(count_query), "results": self.repository.execute_read(cypher), "cypher": cypher.strip()}

    def _high_risk_commerce_results(self):
        cypher = """
            MATCH (t:Transaccion)-[:EN_COMERCIO]->(m:Comercio)
            WHERE m.riesgo = true OR m:AltoRiesgo
            RETURN t.id AS transaccion_id,
                   t.monto AS monto,
                   t.fecha AS fecha,
                   m.id AS comercio_id,
                   m.nombre AS comercio,
                   m.categoria AS categoria
            ORDER BY t.fecha DESC
            LIMIT 25
        """
        count_query = """
            MATCH (t:Transaccion)-[:EN_COMERCIO]->(m:Comercio)
            WHERE m.riesgo = true OR m:AltoRiesgo
            RETURN count(DISTINCT t) AS count
        """
        return {"count": self._count(count_query), "results": self.repository.execute_read(cypher), "cypher": cypher.strip()}

    def _suspicious_locations_results(self):
        cypher = """
            MATCH (t:Transaccion)-[r:DESDE_UBICACION]->(u:Ubicacion)
            WHERE r.es_anomala = true OR r.cambio_pais = true
            RETURN t.id AS transaccion_id,
                   u.ciudad AS ciudad,
                   u.pais AS pais,
                   r.es_anomala AS es_anomala,
                   r.cambio_pais AS cambio_pais
            ORDER BY t.fecha DESC
            LIMIT 25
        """
        count_query = """
            MATCH (t:Transaccion)-[r:DESDE_UBICACION]->(u:Ubicacion)
            WHERE r.es_anomala = true OR r.cambio_pais = true
            RETURN count(DISTINCT t) AS count
        """
        return {"count": self._count(count_query), "results": self.repository.execute_read(cypher), "cypher": cypher.strip()}

    def _suspicious_label_results(self):
        cypher = """
            MATCH (t:Transaccion)
            WHERE t:Sospechosa OR t:Fraudulenta OR t.fraudulenta = true
               OR size(coalesce(t.razones_sospecha, [])) > 0
            OPTIONAL MATCH (t)-[:EN_COMERCIO]->(m:Comercio)
            RETURN t.id AS transaccion_id,
                   labels(t) AS labels,
                   t.fraudulenta AS fraudulenta,
                   t.razones_sospecha AS razones_sospecha,
                   m.id AS comercio_id,
                   m.nombre AS comercio
            ORDER BY t.fecha DESC
            LIMIT 25
        """
        count_query = """
            MATCH (t:Transaccion)
            WHERE t:Sospechosa OR t:Fraudulenta OR t.fraudulenta = true
               OR size(coalesce(t.razones_sospecha, [])) > 0
            RETURN count(DISTINCT t) AS count
        """
        return {"count": self._count(count_query), "results": self.repository.execute_read(cypher), "cypher": cypher.strip()}
