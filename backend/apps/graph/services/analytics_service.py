"""Consultas de dashboard, agregaciones y visualización básica."""

from .neo4j_service import Neo4jRepository
from ..utils.schema import DEMO_QUERIES


class AnalyticsService:
    """Agrupa consultas analíticas de lectura."""

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def dashboard(self):
        query = """
            MATCH (n)
            WITH count(n) AS total_nodos
            MATCH ()-[r]->()
            WITH total_nodos, count(r) AS total_relaciones
            MATCH (t:Transaccion)
            WITH total_nodos, total_relaciones, count(t) AS total_transacciones,
                 sum(CASE WHEN t:Sospechosa OR t:Fraudulenta OR t.fraudulenta = true THEN 1 ELSE 0 END) AS transacciones_sospechosas
            MATCH (a:Alerta)
            RETURN total_nodos, total_relaciones, total_transacciones, transacciones_sospechosas, count(a) AS total_alertas
        """
        result = self.repository.execute_read(query)
        return result[0] if result else {}

    def aggregations(self):
        queries = {
            "riesgo_por_banco": """
                MATCH (:Cuenta)-[:PERTENECE_A]->(b:Banco)
                RETURN b.nombre AS banco, round(avg(b.riesgo), 2) AS riesgo_promedio, count(*) AS cuentas
                ORDER BY riesgo_promedio DESC
            """,
            "monto_por_canal": """
                MATCH (t:Transaccion)
                RETURN t.canal AS canal, round(avg(t.monto), 2) AS promedio, sum(t.monto) AS total
                ORDER BY total DESC
            """,
            "alertas_por_severidad": """
                MATCH (a:Alerta)
                RETURN a.severidad AS severidad, count(*) AS total
                ORDER BY total DESC
            """,
            "clientes_por_nivel_riesgo": """
                MATCH (c:Cliente)
                RETURN c.nivel_riesgo AS nivel, count(*) AS total
                ORDER BY total DESC
            """,
        }
        return {name: self.repository.execute_read(query) for name, query in queries.items()}

    def graph_snapshot(self):
        query = """
            MATCH (a)-[r]->(b)
            RETURN collect(DISTINCT {
                id: a.id,
                labels: labels(a),
                nombre: coalesce(a.nombre, a.id),
                tipo: head(labels(a))
            })[0..120] +
            collect(DISTINCT {
                id: b.id,
                labels: labels(b),
                nombre: coalesce(b.nombre, b.id),
                tipo: head(labels(b))
            })[0..120] AS nodes,
            collect(DISTINCT {
                id: elementId(r),
                source: a.id,
                target: b.id,
                type: type(r)
            })[0..180] AS relationships
        """
        result = self.repository.execute_read(query)
        return result[0] if result else {"nodes": [], "relationships": []}

    def demo_queries(self):
        results = []
        for item in DEMO_QUERIES:
            try:
                data = self.repository.execute_read(item["cypher"])
            except Exception as exc:
                data = [{"error": str(exc)}]
            results.append({"name": item["name"], "cypher": item["cypher"].strip(), "results": data[:20]})
        return results
