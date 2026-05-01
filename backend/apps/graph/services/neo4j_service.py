"""Módulo de conexión y acceso base a Neo4j."""

from typing import Any, Callable

from django.conf import settings
from neo4j import GraphDatabase, exceptions
from rest_framework.exceptions import APIException


class Neo4jConnection:
    """Administra el driver oficial de Neo4j."""

    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = getattr(settings, "NEO4J_URI", None)
            if not uri:
                raise ValueError(
                    "NEO4J_URI is not configured. Set NEO4J_URI in the environment or .env file."
                )
            username = getattr(settings, "NEO4J_USERNAME", None)
            password = getattr(settings, "NEO4J_PASSWORD", None)
            if not username or not password:
                raise ValueError(
                    "NEO4J credentials are incomplete. Set both NEO4J_USERNAME and NEO4J_PASSWORD."
                )
            cls._driver = GraphDatabase.driver(uri, auth=(username, password))
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
        self.database = getattr(settings, "NEO4J_DATABASE", "neo4j")

    def execute_read(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_read(self._run_query, query, parameters or {})
        except exceptions.AuthError as exc:
            raise APIException(
                "Neo4j authentication failed. Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD and NEO4J_DATABASE in backend/.env. "
                "If uses AuraDB, paste the current DB password from the Neo4j console."
            ) from exc
        except exceptions.ServiceUnavailable as exc:
            raise APIException(
                "Neo4j is unreachable. Check NEO4J_URI, network access, and that the database is online."
            ) from exc

    def execute_write(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_write(self._run_query, query, parameters or {})
        except exceptions.AuthError as exc:
            raise APIException(
                "Neo4j authentication failed. Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD and NEO4J_DATABASE in backend/.env. "
                "If uses AuraDB, paste the current DB password from the Neo4j console."
            ) from exc
        except exceptions.ServiceUnavailable as exc:
            raise APIException(
                "Neo4j is unreachable. Check NEO4J_URI, network access, and that the database is online."
            ) from exc

    @staticmethod
    def _run_query(tx, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        result = tx.run(query, parameters)
        return [record.data() for record in result]

    def run_with_handler(self, handler: Callable) -> Any:
        with self.driver.session(database=self.database) as session:
            return session.execute_write(handler)
