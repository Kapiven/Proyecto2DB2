"""Servicios de manipulación de nodos."""

from typing import Any

from .neo4j_service import Neo4jRepository
from ..utils.schema import DYNAMIC_LABELS


class NodeService:
    """CRUD y utilidades para nodos del grafo."""

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def list_nodes(self, label: str | None = None, property_name: str | None = None, property_value: str | None = None):
        if label:
            query = f"MATCH (n:`{label}`) "
        else:
            query = "MATCH (n) "
        if property_name:
            query += f"WHERE toString(n.`{property_name}`) CONTAINS $property_value "
        query += """
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
            ORDER BY properties.id LIMIT 300
        """
        return self.repository.execute_read(query, {"property_value": property_value or ""})

    def create_node(self, labels: list[str], properties: dict[str, Any]):
        label_string = ":".join(f"`{label}`" for label in labels)
        query = f"""
            CREATE (n:{label_string})
            SET n += $properties
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        return self.repository.execute_write(query, {"properties": properties})[0]

    def get_node(self, label: str, node_id: str):
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        result = self.repository.execute_read(query, {"node_id": node_id})
        return result[0] if result else None

    def update_node(self, label: str, node_id: str, properties: dict[str, Any], labels: list[str] | None = None):
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            SET n += $properties
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        updated = self.repository.execute_write(query, {"node_id": node_id, "properties": properties})
        if not updated:
            return None
        if labels:
            self._sync_labels(label, node_id, labels)
        return self.get_node(label, node_id)

    def delete_node(self, label: str, node_id: str):
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            DETACH DELETE n
            RETURN count(*) AS deleted_count
        """
        return self.repository.execute_write(query, {"node_id": node_id})[0]

    def set_property(self, label: str, node_id: str, property_name: str, value: Any):
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            SET n.`{property_name}` = $value
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        result = self.repository.execute_write(query, {"node_id": node_id, "value": value})
        return result[0] if result else None

    def delete_property(self, label: str, node_id: str, property_name: str):
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            REMOVE n.`{property_name}`
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        result = self.repository.execute_write(query, {"node_id": node_id})
        return result[0] if result else None

    def set_properties_bulk(self, label: str, node_ids: list[str], properties: dict[str, Any]):
        query = f"""
            UNWIND $node_ids AS node_id
            MATCH (n:`{label}` {{id: node_id}})
            SET n += $properties
            RETURN count(n) AS updated
        """
        result = self.repository.execute_write(query, {"node_ids": node_ids, "properties": properties})
        return result[0] if result else {"updated": 0}

    def delete_properties_bulk(self, label: str, node_ids: list[str], property_names: list[str]):
        remove_clause = ", ".join(f"n.`{property_name}`" for property_name in property_names)
        query = f"""
            UNWIND $node_ids AS node_id
            MATCH (n:`{label}` {{id: node_id}})
            REMOVE {remove_clause}
            RETURN count(n) AS updated
        """
        result = self.repository.execute_write(query, {"node_ids": node_ids})
        return result[0] if result else {"updated": 0}

    def delete_nodes_bulk(self, label: str, node_ids: list[str]):
        query = f"""
            UNWIND $node_ids AS node_id
            MATCH (n:`{label}` {{id: node_id}})
            DETACH DELETE n
            RETURN count(*) AS deleted
        """
        result = self.repository.execute_write(query, {"node_ids": node_ids})
        return result[0] if result else {"deleted": 0}

    def manage_dynamic_label(self, label: str, node_id: str, dynamic_label: str, action: str):
        allowed = DYNAMIC_LABELS.get(label, [])
        if dynamic_label not in allowed:
            raise ValueError(f"La etiqueta {dynamic_label} no está permitida para {label}.")
        operation = "SET" if action == "add" else "REMOVE"
        query = f"""
            MATCH (n:`{label}` {{id: $node_id}})
            {operation} n:`{dynamic_label}`
            RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS properties
        """
        result = self.repository.execute_write(query, {"node_id": node_id})
        return result[0] if result else None

    def _sync_labels(self, base_label: str, node_id: str, labels: list[str]) -> None:
        allowed_dynamic = DYNAMIC_LABELS.get(base_label, [])
        node = self.get_node(base_label, node_id)
        if not node:
            return
        current_dynamic = [label for label in node["labels"] if label in allowed_dynamic]
        for label in current_dynamic:
            if label not in labels:
                self.manage_dynamic_label(base_label, node_id, label, "remove")
        for label in labels:
            if label in allowed_dynamic and label not in current_dynamic:
                self.manage_dynamic_label(base_label, node_id, label, "add")
