"""Reglas automáticas sencillas para detección de fraude."""

from .neo4j_service import Neo4jRepository


class FraudDetectionService:
    """Aplica heurísticas y crea alertas automáticamente."""

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def available_rules(self):
        return [
            "Múltiples transacciones en ventana de 10 minutos.",
            "Cambio brusco de ubicación en menos de 30 minutos.",
            "Dispositivo compartido entre múltiples clientes.",
            "Comercio de alto riesgo.",
        ]

    def detect(self):
        return {
            "transacciones_rapidas": self._flag_burst_transactions(),
            "cambio_ubicacion": self._flag_location_jumps(),
            "dispositivo_compartido": self._flag_shared_devices(),
            "comercio_alto_riesgo": self._flag_high_risk_commerce(),
        }

    def _flag_burst_transactions(self):
        query = """
            MATCH (c:Cuenta)-[:ORIGINA]->(t1:Transaccion),
                  (c)-[:ORIGINA]->(t2:Transaccion)
            WHERE t1.id <> t2.id
              AND datetime(t2.fecha) > datetime(t1.fecha)
              AND datetime(t2.fecha) <= datetime(t1.fecha) + duration({minutes: 10})
            SET t1:Sospechosa, t2:Sospechosa, t1.fraudulenta = true, t2.fraudulenta = true
            RETURN count(DISTINCT t1) + count(DISTINCT t2) AS total
        """
        result = self.repository.execute_write(query)
        return result[0]["total"] if result else 0

    def _flag_location_jumps(self):
        query = """
            MATCH (c:Cuenta)-[:ORIGINA]->(t1:Transaccion)-[:DESDE_UBICACION]->(u1:Ubicacion),
                  (c)-[:ORIGINA]->(t2:Transaccion)-[:DESDE_UBICACION]->(u2:Ubicacion)
            WHERE t1.id <> t2.id
              AND datetime(t2.fecha) > datetime(t1.fecha)
              AND datetime(t2.fecha) <= datetime(t1.fecha) + duration({minutes: 30})
              AND u1.pais <> u2.pais
            SET t1:Sospechosa, t2:Sospechosa
            RETURN count(DISTINCT t1) + count(DISTINCT t2) AS total
        """
        result = self.repository.execute_write(query)
        return result[0]["total"] if result else 0

    def _flag_shared_devices(self):
        query = """
            MATCH (c1:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(c2:Cliente)
            WHERE c1.id <> c2.id
            MATCH (t:Transaccion)-[:UTILIZA_DISPOSITIVO]->(d)
            SET t:Sospechosa
            RETURN count(DISTINCT t) AS total
        """
        result = self.repository.execute_write(query)
        return result[0]["total"] if result else 0

    def _flag_high_risk_commerce(self):
        query = """
            MATCH (t:Transaccion)-[:EN_COMERCIO]->(m:Comercio)
            WHERE m.riesgo >= 8 OR m:AltoRiesgo
            SET t:Sospechosa
            WITH t
            MERGE (a:Alerta {id: 'AUTO-' + t.id})
            SET a.tipo_alerta = 'Comercio de alto riesgo',
                a.fecha = datetime().toString(),
                a.severidad = 'Alta',
                a.descripcion = 'La transacción ocurrió en un comercio riesgoso',
                a.resuelta = false
            MERGE (t)-[r:GENERA_ALERTA]->(a)
            SET r.score_riesgo = 0.92,
                r.regla_activada = 'comercio_alto_riesgo',
                r.prioridad = 'Alta'
            RETURN count(DISTINCT t) AS total
        """
        result = self.repository.execute_write(query)
        return result[0]["total"] if result else 0
