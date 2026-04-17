"""Vistas de reglas y ejecución de detección de fraude."""

from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.fraud_service import FraudDetectionService


class FraudRulesView(APIView):
    service = FraudDetectionService()

    def get(self, request):
        return Response({"rules": self.service.available_rules()})


class DetectFraudView(APIView):
    service = FraudDetectionService()

    def post(self, request):
        return Response({"detail": "Detección ejecutada", "summary": self.service.detect()})
