"""
Servicios para Graph Data Science (GDS).

Esta implementación centraliza:
1. La proyección del grafo `fraudGraph`.
2. La reutilización de la proyección si ya existe.
3. La recreación explícita cuando el cliente la solicite.
4. La ejecución segura de algoritmos con respuestas JSON listas para frontend.
"""

from .neo4j_service import Neo4jRepository


class GDSService:
    """
    Encapsula toda la lógica de Graph Data Science.

    En GDS no se ejecutan algoritmos directamente sobre el grafo persistido.
    Antes hay que proyectar un subgrafo en memoria; esa proyección es mucho
    más eficiente para algoritmos como PageRank, Louvain o Dijkstra.
    """

    GRAPH_NAME = "fraudGraph"

    GRAPH_PROJECTION_QUERY = """
        CALL gds.graph.project(
            $graph_name,
            ['Cliente', 'Cuenta', 'Transaccion', 'Dispositivo', 'Comercio'],
            {
                ORIGINA: {orientation: 'NATURAL'},
                DESTINADA_A: {orientation: 'NATURAL'},
                UTILIZA_DISPOSITIVO: {orientation: 'NATURAL'},
                EN_COMERCIO: {orientation: 'NATURAL'}
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
    """

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def run(self, algorithm: str, source_id: str | None = None, target_id: str | None = None) -> dict:
        """
        Mantiene compatibilidad con el endpoint genérico existente.

        Aunque ahora hay endpoints dedicados por algoritmo, esta función
        evita romper clientes anteriores que aún consuman `gds/run/`.
        """
        mapping = {
            "pagerank": self.page_rank,
            "louvain": self.louvain,
            "node_similarity": self.node_similarity,
            "shortest_path": lambda: self.shortest_path(source_id or "", target_id or ""),
        }
        return mapping[algorithm]()

    def graph_exists(self) -> dict:
        """
        Verifica si la proyección en memoria ya existe.

        Se consulta antes de crear el grafo para evitar recrearlo en cada
        llamada y desperdiciar recursos del motor GDS.
        """
        query = """
            CALL gds.graph.exists($graph_name)
            YIELD exists
            RETURN exists
        """
        result = self.repository.execute_read(query, {"graph_name": self.GRAPH_NAME})
        exists = bool(result and result[0]["exists"])
        return {"graphName": self.GRAPH_NAME, "exists": exists}

    def project_graph(self, force_recreate: bool = False) -> dict:
        """
        Proyecta el grafo requerido por los algoritmos.

        Si el grafo ya existe se reutiliza. Si `force_recreate` es verdadero,
        se elimina primero y luego se vuelve a proyectar.
        """
        exists_info = self.graph_exists()

        if exists_info["exists"] and not force_recreate:
            return {
                "graphName": self.GRAPH_NAME,
                "created": False,
                "message": "La proyección ya existía y fue reutilizada.",
                "exists": True,
            }

        if exists_info["exists"] and force_recreate:
            self.drop_graph()

        try:
            result = self.repository.execute_write(
                self.GRAPH_PROJECTION_QUERY,
                {"graph_name": self.GRAPH_NAME},
            )
        except Exception as exc:
            raise RuntimeError(f"No se pudo proyectar el grafo GDS: {exc}") from exc

        payload = result[0] if result else {}
        return {
            "graphName": payload.get("graphName", self.GRAPH_NAME),
            "created": True,
            "message": "Proyección GDS creada correctamente.",
            "nodeCount": payload.get("nodeCount", 0),
            "relationshipCount": payload.get("relationshipCount", 0),
            "exists": True,
        }

    def ensure_projected_graph(self) -> dict:
        """
        Garantiza que el grafo exista antes de correr cualquier algoritmo.

        Este comportamiento cumple con el requisito de autocreación si la
        proyección aún no fue generada.
        """
        exists_info = self.graph_exists()
        if exists_info["exists"]:
            return {
                "graphName": self.GRAPH_NAME,
                "created": False,
                "message": "La proyección GDS ya estaba disponible.",
                "exists": True,
            }
        return self.project_graph()

    def drop_graph(self) -> dict:
        """
        Elimina la proyección de memoria.

        Esto no borra datos persistidos de Neo4j; solo libera el grafo GDS.
        """
        exists_info = self.graph_exists()
        if not exists_info["exists"]:
            return {
                "graphName": self.GRAPH_NAME,
                "dropped": False,
                "message": "La proyección no existía.",
            }

        try:
            result = self.repository.execute_write(
                """
                CALL gds.graph.drop($graph_name)
                YIELD graphName
                RETURN graphName
                """,
                {"graph_name": self.GRAPH_NAME},
            )
        except Exception as exc:
            raise RuntimeError(f"No se pudo eliminar la proyección GDS: {exc}") from exc

        return {
            "graphName": result[0].get("graphName", self.GRAPH_NAME) if result else self.GRAPH_NAME,
            "dropped": True,
            "message": "Proyección GDS eliminada correctamente.",
        }

    def page_rank(self) -> dict:
        """
        Calcula PageRank.

        Este algoritmo identifica nodos influyentes según su posición en la
        red y devuelve los 20 nodos con mayor score.
        """
        self.ensure_projected_graph()
        query = """
            CALL gds.pageRank.stream($graph_name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   round(score, 4) AS score
            ORDER BY score DESC
            LIMIT 20
        """
        return self._run_algorithm("pagerank", query)

    def louvain(self) -> dict:
        """
        Detecta comunidades con Louvain.

        Devuelve el identificador del nodo y la comunidad a la que fue
        asignado según la estructura del grafo proyectado.
        """
        self.ensure_projected_graph()
        query = """
            CALL gds.louvain.stream($graph_name)
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   communityId
            ORDER BY communityId, id
        """
        return self._run_algorithm("louvain", query)

    def node_similarity(self) -> dict:
        """
        Ejecuta Node Similarity.

        Este algoritmo encuentra pares de nodos con patrones de conexión
        similares y devuelve los 20 pares con mayor similitud.
        """
        self.ensure_projected_graph()
        query = """
            CALL gds.nodeSimilarity.stream($graph_name)
            YIELD node1, node2, similarity
            RETURN gds.util.asNode(node1).id AS node1,
                   gds.util.asNode(node2).id AS node2,
                   round(similarity, 4) AS similarity
            ORDER BY similarity DESC
            LIMIT 20
        """
        return self._run_algorithm("node_similarity", query)

    def shortest_path(self, source_id: str, target_id: str) -> dict:
        """
        Calcula la ruta más corta entre dos clientes con Dijkstra.

        La API devuelve el costo total y la ruta para que el frontend pueda
        representarla sin procesamiento adicional.
        """
        if not source_id or not target_id:
            raise ValueError("source_id y target_id son obligatorios para shortest_path.")

        self.ensure_projected_graph()
        query = """
            MATCH (a:Cliente {id: $source_id}), (b:Cliente {id: $target_id})
            CALL gds.shortestPath.dijkstra.stream($graph_name, {
                sourceNode: id(a),
                targetNode: id(b)
            })
            YIELD totalCost, nodeIds
            RETURN totalCost,
                   [nodeId IN nodeIds | gds.util.asNode(nodeId).id] AS path
        """
        return self._run_algorithm(
            "shortest_path",
            query,
            {
                "graph_name": self.GRAPH_NAME,
                "source_id": source_id,
                "target_id": target_id,
            },
        )

    def _run_algorithm(self, algorithm: str, query: str, params: dict | None = None) -> dict:
        """
        Ejecuta un algoritmo GDS y estandariza la respuesta.

        Si el motor GDS falla, se propaga un error claro para que la vista
        responda con JSON útil al frontend.
        """
        params = {"graph_name": self.GRAPH_NAME, **(params or {})}
        try:
            results = self.repository.execute_read(query, params)
            return {
                "algorithm": algorithm,
                "graphName": self.GRAPH_NAME,
                "results": results,
            }
        except Exception as exc:
            raise RuntimeError(f"Falló la ejecución de {algorithm} en GDS: {exc}") from exc
