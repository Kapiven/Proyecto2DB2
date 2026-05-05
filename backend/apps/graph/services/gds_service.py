"""Servicios para Graph Data Science (GDS) en Neo4j Aura."""

from .neo4j_service import Neo4jRepository



class GDSService:
    """Encapsula proyeccion Aura GDS, algoritmos y fallbacks Cypher."""

    GRAPH_NAME = "fraudGraph"
    SESSION_NAME = "fraud-session"
    SESSION_MEMORY = "2GB"

    REQUIRED_LABELS = {
        "Cliente",
        "Cuenta",
        "Transaccion",
        "Dispositivo",
        "Ubicacion",
        "Comercio",
        "Banco",
        "Alerta",
    }

    REQUIRED_RELATIONSHIPS = {
        "TIENE_CUENTA",
        "USA_DISPOSITIVO",
        "ORIGINA",
        "UTILIZA_DISPOSITIVO",
        "DESDE_UBICACION",
        "EN_COMERCIO",
        "PERTENECE_A",
    }

    def __init__(self) -> None:
        self.repository = Neo4jRepository()
        self._session_id: str | None = None

    def run(self, algorithm: str, source_id: str | None = None, target_id: str | None = None) -> dict:
        mapping = {
            "pagerank": self.page_rank,
            "louvain": self.louvain,
            "node_similarity": self.node_similarity,
            "shortest_path": lambda: self.shortest_path(source_id or "", target_id or ""),
        }
        return mapping[algorithm]()

    def schema_status(self) -> dict:
        """Lee el esquema real antes de ejecutar consultas de negocio."""
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

    def graph_exists(self) -> dict:
        query = """
            CALL gds.graph.exists($graph_name)
            YIELD graphName, exists
            RETURN graphName, exists
        """
        try:
            result = self.repository.execute_read(query, {"graph_name": self.GRAPH_NAME})
            exists = bool(result and result[0].get("exists"))
            return {"graphName": self.GRAPH_NAME, "exists": exists}
        except Exception as exc:
            return {"graphName": self.GRAPH_NAME, "exists": False, "error": str(exc)}

    def status(self) -> dict:
        session = self._get_or_create_session()
        graph = self.graph_exists()
        return {
            "graphName": self.GRAPH_NAME,
            "session": session,
            "graph": graph,
            "schema": self.schema_status(),
        }

    def _get_or_create_session(self) -> dict:
        query = """
            CALL gds.session.getOrCreate(
              $session_name,
              $memory,
              duration({minutes: 30})
            )
            YIELD id, name, memory, status, expiryDate, ttl, errorMessage
            RETURN id, name, memory, status, expiryDate, ttl, errorMessage
        """
        result = self.repository.execute_write(
            query,
            {"session_name": self.SESSION_NAME, "memory": self.SESSION_MEMORY},
        )
        session = result[0] if result else {"name": self.SESSION_NAME}
        self._session_id = session.get("id") or session.get("name") or self.SESSION_NAME
        return session

    def project_graph(self, force_recreate: bool = False) -> dict:
        exists_info = self.graph_exists()
        if exists_info.get("exists") and not force_recreate:
            return {
                "graphName": self.GRAPH_NAME,
                "created": False,
                "exists": True,
                "message": "La proyeccion GDS ya existia y fue reutilizada.",
                "session": self._get_or_create_session(),
            }

        if exists_info.get("exists") and force_recreate:
            self.drop_graph()

        session = self._get_or_create_session()
        session_id = session.get("id") or session.get("name") or self.SESSION_NAME
        query = """
            CYPHER runtime=parallel
            MATCH (source)
            OPTIONAL MATCH (source)-[r]->(target)
            RETURN gds.graph.project(
              $graph_name,
              source,
              target,
              {},
              { sessionId: $session_id }
            ) AS graph
        """
        result = self.repository.execute_write(
            query,
            {"graph_name": self.GRAPH_NAME, "session_id": session_id},
        )
        graph = result[0].get("graph", {}) if result else {}
        return {
            "graphName": graph.get("graphName", self.GRAPH_NAME),
            "created": True,
            "exists": True,
            "used_gds": True,
            "fallback": False,
            "message": "Proyeccion Aura GDS creada con Cypher projection y sesion.",
            "nodeCount": graph.get("nodeCount", 0),
            "relationshipCount": graph.get("relationshipCount", 0),
            "session": session,
            "schema": self.schema_status(),
        }

    def ensure_gds_graph(self) -> dict:
        exists_info = self.graph_exists()
        if exists_info.get("exists"):
            return {
                "graphName": self.GRAPH_NAME,
                "created": False,
                "exists": True,
                "message": "La proyeccion GDS ya estaba disponible.",
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
                "message": "La proyeccion no existia.",
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
            "message": "Proyeccion GDS eliminada correctamente.",
        }

    def page_rank(self) -> dict:
        query = """
            CALL gds.pageRank.stream($graph_name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   round(score, 4) AS score
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
        return self._run_algorithm("pagerank", query, fallback)

    def louvain(self) -> dict:
        query = """
            CALL gds.louvain.stream($graph_name)
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).id AS id,
                   labels(gds.util.asNode(nodeId)) AS labels,
                   communityId
            ORDER BY communityId, id
            LIMIT 50
        """
        fallback = """
            MATCH (c:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)
            RETURN c.id AS id, labels(c) AS labels, d.id AS communityId
            ORDER BY communityId, id
            LIMIT 50
        """
        return self._run_algorithm("louvain", query, fallback)

    def node_similarity(self) -> dict:
        query = """
            CALL gds.nodeSimilarity.stream($graph_name)
            YIELD node1, node2, similarity
            RETURN gds.util.asNode(node1).id AS node1,
                   gds.util.asNode(node2).id AS node2,
                   round(similarity, 4) AS similarity
            ORDER BY similarity DESC
            LIMIT 20
        """
        fallback = """
            MATCH (c1:Cliente)-[:USA_DISPOSITIVO]->(d:Dispositivo)<-[:USA_DISPOSITIVO]-(c2:Cliente)
            WHERE c1.id < c2.id
            RETURN c1.id AS node1, c2.id AS node2,
                   count(DISTINCT d) AS shared_devices,
                   round(1.0 / count(DISTINCT d), 4) AS similarity
            ORDER BY shared_devices DESC
            LIMIT 20
        """
        return self._run_algorithm("node_similarity", query, fallback)

    def shortest_path(self, source_id: str, target_id: str) -> dict:
        if not source_id or not target_id:
            raise ValueError("source_id y target_id son obligatorios para shortest_path.")

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
        fallback = """
            MATCH (a:Cliente {id: $source_id}), (b:Cliente {id: $target_id})
            MATCH p = shortestPath((a)-[*..8]-(b))
            RETURN length(p) AS totalCost, [node IN nodes(p) | node.id] AS path
        """
        return self._run_algorithm(
            "shortest_path",
            query,
            fallback,
            {"source_id": source_id, "target_id": target_id},
        )

    def _run_algorithm(
        self,
        algorithm: str,
        gds_query: str,
        fallback_query: str,
        params: dict | None = None,
    ) -> dict:
        params = {"graph_name": self.GRAPH_NAME, **(params or {})}
        try:
            projection = self.ensure_gds_graph()
            results = self.repository.execute_read(gds_query, params)
            return {
                "algorithm": algorithm,
                "graphName": self.GRAPH_NAME,
                "used_gds": True,
                "fallback": False,
                "projection": projection,
                "results": results,
            }
        except Exception as exc:
            fallback_results = self.repository.execute_read(fallback_query, params)
            return {
                "algorithm": algorithm,
                "graphName": self.GRAPH_NAME,
                "used_gds": False,
                "fallback": True,
                "gds_error": str(exc),
                "results": fallback_results,
            }
