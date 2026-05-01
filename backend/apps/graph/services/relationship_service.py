"""Servicios para CRUD de relaciones y sus propiedades."""

from typing import Any

from .neo4j_service import Neo4jRepository


class RelationshipService:
    """Maneja relaciones con `elementId`."""

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def list_relationships(self, relationship_type: str | None = None):
        type_filter = f":`{relationship_type}`" if relationship_type else ""
        query = f"""
            MATCH (a)-[r{type_filter}]->(b)
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
            LIMIT 300
        """
        return self.repository.execute_read(query)

    def create_relationship(self, relationship_type: str, start_label: str, start_node_id: str, end_label: str, end_node_id: str, properties: dict[str, Any]):
        query = f"""
            MATCH (a:`{start_label}` {{id: $start_node_id}})
            MATCH (b:`{end_label}` {{id: $end_node_id}})
            CREATE (a)-[r:`{relationship_type}`]->(b)
            SET r += $properties
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
        """
        result = self.repository.execute_write(query, {"start_node_id": start_node_id, "end_node_id": end_node_id, "properties": properties})
        return result[0] if result else None

    def get_relationship(self, relationship_id: str):
        query = """
            MATCH (a)-[r]->(b)
            WHERE elementId(r) = $relationship_id
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
        """
        result = self.repository.execute_read(query, {"relationship_id": relationship_id})
        return result[0] if result else None

    def update_relationship(self, relationship_id: str, properties: dict[str, Any]):
        query = """
            MATCH (a)-[r]->(b)
            WHERE elementId(r) = $relationship_id
            SET r += $properties
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
        """
        result = self.repository.execute_write(query, {"relationship_id": relationship_id, "properties": properties})
        return result[0] if result else None

    def delete_relationship(self, relationship_id: str):
        query = """
            MATCH ()-[r]->()
            WHERE elementId(r) = $relationship_id
            DELETE r
            RETURN count(*) AS deleted_count
        """
        return self.repository.execute_write(query, {"relationship_id": relationship_id})[0]

    def set_property(self, relationship_id: str, property_name: str, value: Any):
        query = f"""
            MATCH (a)-[r]->(b)
            WHERE elementId(r) = $relationship_id
            SET r.`{property_name}` = $value
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
        """
        result = self.repository.execute_write(query, {"relationship_id": relationship_id, "value": value})
        return result[0] if result else None

    def delete_property(self, relationship_id: str, property_name: str):
        query = f"""
            MATCH (a)-[r]->(b)
            WHERE elementId(r) = $relationship_id
            REMOVE r.`{property_name}`
            RETURN elementId(r) AS relationship_id,
                   type(r) AS relationship_type,
                   a.id AS start_node_id,
                   labels(a) AS start_labels,
                   b.id AS end_node_id,
                   labels(b) AS end_labels,
                   properties(r) AS properties
        """
        result = self.repository.execute_write(query, {"relationship_id": relationship_id})
        return result[0] if result else None

    def set_properties_bulk(self, relationship_ids: list[str], properties: dict[str, Any]):
        query = f"""
            UNWIND $relationship_ids AS relationship_id
            MATCH ()-[r]->()
            WHERE elementId(r) = toInteger(relationship_id)
            SET r += $properties
            RETURN count(r) AS updated
        """
        result = self.repository.execute_write(query, {"relationship_ids": relationship_ids, "properties": properties})
        return result[0] if result else {"updated": 0}

    def delete_properties_bulk(self, relationship_ids: list[str], property_names: list[str]):
        remove_clause = ", ".join(f"r.`{property_name}`" for property_name in property_names)
        query = f"""
            UNWIND $relationship_ids AS relationship_id
            MATCH ()-[r]->()
            WHERE elementId(r) = toInteger(relationship_id)
            REMOVE {remove_clause}
            RETURN count(r) AS updated
        """
        result = self.repository.execute_write(query, {"relationship_ids": relationship_ids})
        return result[0] if result else {"updated": 0}

    def delete_relationships_bulk(self, relationship_ids: list[str]):
        query = f"""
            UNWIND $relationship_ids AS relationship_id
            MATCH ()-[r]->()
            WHERE elementId(r) = toInteger(relationship_id)
            DELETE r
            RETURN count(*) AS deleted
        """
        result = self.repository.execute_write(query, {"relationship_ids": relationship_ids})
        return result[0] if result else {"deleted": 0}
