"""Módulo de conexión y acceso base a Neo4j."""

import os
from typing import Any, Callable

from neo4j import GraphDatabase


class Neo4jConnection:
    """Administra el driver oficial de Neo4j."""

    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI")
            if not uri:
                raise ValueError(
                    "NEO4J_URI is not configured. Set the environment variable before starting the application."
                )
            username = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")
            auth = (username, password) if username or password else None
            cls._driver = GraphDatabase.driver(uri, auth=auth)
        return cls._driver

    @classmethod
    def verify(cls) -> None:
        cls.get_driver().verify_connectivity()

    @classmethod
    def close(cls) -> None:
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None


class Neo4jRepository:
    """Repositorio base con helpers para lectura/escritura."""

    def __init__(self) -> None:
        self.driver = Neo4jConnection.get_driver()
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

    def execute_read(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            return session.execute_read(self._run_query, query, parameters or {})

    def execute_write(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            return session.execute_write(self._run_query, query, parameters or {})

    @staticmethod
    def _run_query(tx, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        result = tx.run(query, parameters)
        return [record.data() for record in result]

    def run_with_handler(self, handler: Callable) -> Any:
        with self.driver.session(database=self.database) as session:
            return session.execute_write(handler)
