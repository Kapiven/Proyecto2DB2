"""Vistas para CRUD de relaciones y propiedades."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import (
    BulkRelationshipDeleteSerializer,
    BulkRelationshipPropertyRemoveSerializer,
    BulkRelationshipPropertySerializer,
    RelationshipPropertySerializer,
    RelationshipSerializer,
)
from ..services.relationship_service import RelationshipService


class RelationshipListView(APIView):
    def get(self, request):
        service = RelationshipService()
        return Response(service.list_relationships(request.query_params.get("relationship_type")))

    def post(self, request):
        serializer = RelationshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        created = service.create_relationship(**serializer.validated_data)
        return Response(created, status=status.HTTP_201_CREATED)


class RelationshipDetailView(APIView):
    def get(self, request, relationship_id):
        service = RelationshipService()
        item = service.get_relationship(relationship_id)
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def put(self, request, relationship_id):
        serializer = RelationshipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        item = service.update_relationship(relationship_id, serializer.validated_data["properties"])
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def delete(self, request, relationship_id):
        service = RelationshipService()
        return Response(service.delete_relationship(relationship_id))


class RelationshipPropertyView(APIView):
    def put(self, request, relationship_id, property_name):
        serializer = RelationshipPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        item = service.set_property(relationship_id, property_name, serializer.validated_data["value"])
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    def delete(self, request, relationship_id, property_name):
        service = RelationshipService()
        item = service.delete_property(relationship_id, property_name)
        if not item:
            return Response({"detail": "Relación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(item)


class RelationshipPropertyBatchView(APIView):
    def post(self, request):
        serializer = BulkRelationshipPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        result = service.set_properties_bulk(
            serializer.validated_data["relationship_ids"],
            serializer.validated_data["properties"],
        )
        return Response(result)

    def delete(self, request):
        serializer = BulkRelationshipPropertyRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        result = service.delete_properties_bulk(
            serializer.validated_data["relationship_ids"],
            serializer.validated_data["property_names"],
        )
        return Response(result)


class RelationshipDeleteBatchView(APIView):
    def post(self, request):
        serializer = BulkRelationshipDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = RelationshipService()
        result = service.delete_relationships_bulk(serializer.validated_data["relationship_ids"])
        return Response(result)
