"""Vistas para bootstrap, carga CSV e inserción masiva."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import CSVUploadSerializer, FakeDataSerializer
from ..services.ingestion_service import IngestionService
from ..services.neo4j_service import Neo4jConnection


class SchemaBootstrapView(APIView):
    service = IngestionService()

    def post(self, request):
        Neo4jConnection.verify()
        return Response({"detail": "Conexión verificada", "results": self.service.bootstrap_constraints()})


class CSVUploadView(APIView):
    service = IngestionService()

    def post(self, request):
        serializer = CSVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        result = self.service.import_csv(serializer.validated_data["entity_type"], file.read())
        return Response({"detail": "Archivo procesado correctamente", "result": result}, status=status.HTTP_201_CREATED)


class FakeDataGenerationView(APIView):
    service = IngestionService()

    def post(self, request):
        serializer = FakeDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.service.generate_fake_data(**serializer.validated_data)
        return Response({"detail": "Datos sintéticos generados", "result": result}, status=status.HTTP_201_CREATED)
