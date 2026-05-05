"""Vistas para CRUD de relaciones y propiedades."""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import (
    BulkRelationshipDeleteSerializer,
    RelationshipPropertySerializer,
    RelationshipSerializer,
)
from ..services.relationship_service import RelationshipService

logger = logging.getLogger(__name__)


class RelationshipListView(APIView):
    service = RelationshipService()

    def get(self, request):
        return Response(self.service.list_relationships(request.query_params.get("relationship_type")))

    def post(self, request):
        serializer = RelationshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = self.service.create_relationship(**serializer.validated_data)
        return Response(created, status=status.HTTP_201_CREATED)


class RelationshipDetailView(APIView):
    service = RelationshipService()

    def get(self, request, relationship_id):
        item = self.service.get_relationship(relationship_id)
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def put(self, request, relationship_id):
        serializer = RelationshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = self.service.update_relationship(relationship_id, serializer.validated_data["properties"])
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def delete(self, request, relationship_id):
        return Response(self.service.delete_relationship(relationship_id))


class RelationshipPropertyView(APIView):
    service = RelationshipService()

    def put(self, request, relationship_id, property_name):
        serializer = RelationshipPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = self.service.set_property(relationship_id, property_name, serializer.validated_data["value"])
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def delete(self, request, relationship_id, property_name):
        item = self.service.delete_property(relationship_id, property_name)
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)


class RelationshipPropertyBatchView(APIView):
    def post(self, request):
        logger.info("Batch relationship property update request.data=%s", request.data)
        relationship_ids = request.data["relationship_ids"]
        properties = request.data["properties"]
        logger.info(
            "Batch relationship property update parsed relationship_ids=%s properties=%s property_types=%s",
            relationship_ids,
            properties,
            {key: type(value).__name__ for key, value in properties.items()},
        )
        service = RelationshipService()
        result = service.set_properties_bulk(relationship_ids, properties)
        if result.get("updated", 0) == 0:
            return Response(
                {
                    "error": True,
                    "updated": 0,
                    "message": result.get("message", "No relationships matched the provided IDs"),
                    "relationships": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)

    def delete(self, request):
        relationship_ids = request.data["relationship_ids"]
        property_names = request.data["property_names"]
        service = RelationshipService()
        result = service.delete_properties_bulk(relationship_ids, property_names)
        if result.get("updated", 0) == 0:
            return Response(
                {
                    "error": True,
                    "updated": 0,
                    "message": result.get("message", "No relationships matched the provided IDs"),
                    "relationships": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)


class RelationshipDeleteBatchView(APIView):
    def post(self, request):
        serializer = BulkRelationshipDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        result = service.delete_relationships_bulk(serializer.validated_data["relationship_ids"])
        if result.get("deleted", 0) == 0:
            return Response(
                {
                    "error": True,
                    "deleted": 0,
                    "message": result.get("message", "No relationships matched the provided IDs"),
                    "relationships": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)
