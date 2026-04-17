"""Vistas para CRUD de relaciones y propiedades."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import RelationshipPropertySerializer, RelationshipSerializer
from ..services.relationship_service import RelationshipService


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
