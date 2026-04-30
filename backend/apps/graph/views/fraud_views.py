"""Vistas de reglas y ejecución de detección de fraude."""

from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.fraud_service import FraudDetectionService


class FraudRulesView(APIView):
    def get(self, request):
        service = FraudDetectionService()
        return Response({"rules": service.available_rules()})


class DetectFraudView(APIView):
    def post(self, request):
        service = FraudDetectionService()
        return Response({"detail": "Detección ejecutada", "summary": service.detect()})
