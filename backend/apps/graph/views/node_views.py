"""Vistas para CRUD de nodos y etiquetas dinámicas."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import DynamicLabelSerializer, NodePropertySerializer, NodeSerializer
from ..services.node_service import NodeService


class NodeListView(APIView):
    def get(self, request):
        service = NodeService()
        data = service.list_nodes(request.query_params.get("label"), request.query_params.get("property_name"), request.query_params.get("property_value"))
        return Response(data)

    def post(self, request):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = NodeService()
        created = service.create_node(**serializer.validated_data)
        return Response(created, status=status.HTTP_201_CREATED)


class NodeDetailView(APIView):
    def get(self, request, label, node_id):
        service = NodeService()
        node = service.get_node(label, node_id)
        if not node:
            return Response({"detail": "Nodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)

    def put(self, request, label, node_id):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = NodeService()
        node = service.update_node(label, node_id, serializer.validated_data["properties"], serializer.validated_data["labels"])
        if not node:
            return Response({"detail": "Nodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)

    def delete(self, request, label, node_id):
        service = NodeService()
        return Response(service.delete_node(label, node_id))


class NodePropertyView(APIView):
    def put(self, request, label, node_id, property_name):
        serializer = NodePropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = NodeService()
        node = service.set_property(label, node_id, property_name, serializer.validated_data["value"])
        if not node:
            return Response({"detail": "Nodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)

    def delete(self, request, label, node_id, property_name):
        service = NodeService()
        node = service.delete_property(label, node_id, property_name)
        if not node:
            return Response({"detail": "Nodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)


class DynamicLabelView(APIView):
    def post(self, request, label, node_id):
        serializer = DynamicLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = NodeService()
        try:
            node = service.manage_dynamic_label(label, node_id, serializer.validated_data["label"], serializer.validated_data["action"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not node:
            return Response({"detail": "Nodo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)
