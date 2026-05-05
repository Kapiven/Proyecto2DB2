"""Servicios para Graph Data Science (GDS) en Neo4j Desktop local."""

from .neo4j_service import Neo4jRepository


class GDSService:
    """Proyecta el grafo local GDS, ejecuta algoritmos y conserva fallbacks."""

    GRAPH_NAME = "fraudGraph"

    NODE_LABELS = [
        "Cliente",
        "Cuenta",
        "Transaccion",
        "Dispositivo",
        "Comercio",
        "Banco",
        "Alerta",
        "Tarjeta",
        "Ubicacion",
    ]

    RELATIONSHIP_TYPES = [
        "TIENE_CUENTA",
        "USA_DISPOSITIVO",
        "TIENE_TARJETA",
        "ORIGINA",
        "DESTINADA_A",
        "UTILIZA_DISPOSITIVO",
        "DESDE_UBICACION",
        "EN_COMERCIO",
        "UTILIZA_TARJETA",
        "GENERA_ALERTA",
        "PERTENECE_A",
        "LOCALIZADO_EN",
    ]

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def run(self, algorithm: str, source_id: str | None = None, target_id: str | None = None) -> dict:
        mapping = {
            "pagerank": self.page_rank,
            "louvain": self.louvain,
            "node_similarity": self.node_similarity,
            "shortest_path": lambda: self.shortest_path(source_id or "", target_id or ""),
        }
        return mapping[algorithm]()

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
            "missingLabels": sorted(set(self.NODE_LABELS) - current_labels),
            "missingRelationshipTypes": sorted(set(self.RELATIONSHIP_TYPES) - current_rels),
            "removedLegacyLabels": sorted(current_labels & {"Actor", "Movie", "Person", "Film"}),
        }

    def graph_exists(self) -> dict:
        query = """
            CALL gds.graph.exists($graph_name)
            YIELD graphName, exists
            RETURN graphName, exists
        """
        result = self.repository.execute_read(query, {"graph_name": self.GRAPH_NAME})
        exists = bool(result and result[0].get("exists"))
        return {"graphName": self.GRAPH_NAME, "exists": exists}

    def status(self) -> dict:
        graph = self.graph_exists()
        return {
            "graphName": self.GRAPH_NAME,
            "graph": graph,
            "schema": self.schema_status(),
        }

    def project_graph(self, force_recreate: bool = False) -> dict:
        exists_info = self.graph_exists()
        if exists_info.get("exists") and not force_recreate:
            return {
                "graphName": self.GRAPH_NAME,
                "exists": True,
                "created": False,
                "message": "Graph already projected",
            }

        if exists_info.get("exists") and force_recreate:
            self.drop_graph()

        query = """
            CALL gds.graph.project(
              $graph_name,
              $node_labels,
              $relationship_types
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
        """
        result = self.repository.execute_write(
            query,
            {
                "graph_name": self.GRAPH_NAME,
                "node_labels": self.NODE_LABELS,
                "relationship_types": self.RELATIONSHIP_TYPES,
            },
        )
        payload = result[0] if result else {}
        return {
            "graphName": payload.get("graphName", self.GRAPH_NAME),
            "exists": True,
            "created": True,
            "used_gds": True,
            "fallback": False,
            "message": "Graph projected",
            "nodeCount": payload.get("nodeCount", 0),
            "relationshipCount": payload.get("relationshipCount", 0),
        }

    def ensure_gds_graph(self) -> dict:
        exists_info = self.graph_exists()
        if exists_info.get("exists"):
            return {
                "graphName": self.GRAPH_NAME,
                "exists": True,
                "created": False,
                "message": "Graph already projected",
            }
        return self.project_graph()

    def ensure_projected_graph(self) -> dict:
        return self.ensure_gds_graph()

    def drop_graph(self) -> dict:
        exists_info = self.graph_exists()
        if not exists_info.get("exists"):
            return {
                "graphName": self.GRAPH_NAME,
                "dropped": False,
                "message": "Graph was not projected",
            }

        result = self.repository.execute_write(
            """
            CALL gds.graph.drop($graph_name)
            YIELD graphName
            RETURN graphName
            """,
            {"graph_name": self.GRAPH_NAME},
        )
        return {
            "graphName": result[0].get("graphName", self.GRAPH_NAME) if result else self.GRAPH_NAME,
            "dropped": True,
            "message": "Graph projection dropped",
        }

    def page_rank(self) -> dict:
        query = """
            CALL gds.pageRank.stream($graph_name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   score
            ORDER BY score DESC
            LIMIT 20
        """
        fallback = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            RETURN n.id AS id, labels(n) AS labels, count(r) AS score
            ORDER BY score DESC
            LIMIT 20
        """
        return self._run_gds_algorithm("pagerank", query, fallback)

    def louvain(self) -> dict:
        query = """
            CALL gds.louvain.stream($graph_name)
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   communityId
            ORDER BY communityId
            LIMIT 50
        """
        fallback = """
            MATCH (c:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)
            RETURN c.id AS id, labels(c) AS labels, d.id AS communityId
            ORDER BY communityId
            LIMIT 50
        """
        return self._run_gds_algorithm("louvain", query, fallback)

    def node_similarity(self) -> dict:
        query = """
            CALL gds.nodeSimilarity.stream($graph_name)
            YIELD node1, node2, similarity
            RETURN gds.util.asNode(node1).id AS node1_id,
                   gds.util.asNode(node2).id AS node2_id,
                   similarity
            ORDER BY similarity DESC
            LIMIT 20
        """
        fallback = """
            MATCH (c1:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(c2:Cliente)
            WHERE c1.id < c2.id
            RETURN c1.id AS node1_id, c2.id AS node2_id,
                   count(DISTINCT d) AS shared_devices,
                   1.0 AS similarity
            ORDER BY shared_devices DESC
            LIMIT 20
        """
        return self._run_gds_algorithm("node_similarity", query, fallback)

    def shortest_path(self, source_id: str, target_id: str) -> dict:
        if not source_id or not target_id:
            raise ValueError("source_id y target_id son obligatorios para shortest_path.")

        fallback = """
            MATCH (a:Cliente {id: $source_id}), (b:Cliente {id: $target_id})
            MATCH p = shortestPath((a)-[*..8]-(b))
            RETURN length(p) AS totalCost, [node IN nodes(p) | node.id] AS path
        """
        params = {"source_id": source_id, "target_id": target_id}
        try:
            projection = self.ensure_gds_graph()
            data = self.repository.execute_read(fallback, params)
            return self._response(
                "shortest_path",
                data,
                used_gds=False,
                fallback=True,
                projection=projection,
                message="Cypher shortestPath used because weighted GDS path projection is not configured.",
            )
        except Exception as exc:
            return self._response(
                "shortest_path",
                [],
                used_gds=False,
                fallback=True,
                gds_error=str(exc),
            )

    def _run_gds_algorithm(
        self,
        algorithm: str,
        gds_query: str,
        fallback_query: str,
        params: dict | None = None,
    ) -> dict:
        params = {"graph_name": self.GRAPH_NAME, **(params or {})}
        try:
            projection = self.ensure_gds_graph()
            data = self.repository.execute_read(gds_query, params)
            return self._response(
                algorithm,
                data,
                used_gds=True,
                fallback=False,
                projection=projection,
            )
        except Exception as exc:
            fallback_data = self.repository.execute_read(fallback_query, params)
            return self._response(
                algorithm,
                fallback_data,
                used_gds=False,
                fallback=True,
                gds_error=str(exc),
            )

    def _response(
        self,
        algorithm: str,
        data: list[dict],
        used_gds: bool,
        fallback: bool,
        projection: dict | None = None,
        gds_error: str | None = None,
        message: str | None = None,
    ) -> dict:
        payload = {
            "algorithm": algorithm,
            "graphName": self.GRAPH_NAME,
            "used_gds": used_gds,
            "fallback": fallback,
            "data": data,
            "results": data,
        }
        if projection is not None:
            payload["projection"] = projection
        if gds_error:
            payload["gds_error"] = gds_error
        if message:
            payload["message"] = message
        return payload
