"""Vistas de reglas y ejecucion de deteccion de fraude."""

from datetime import datetime

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.fraud_service import FraudDetectionService


class FraudRulesView(APIView):
    service = FraudDetectionService()

    def get(self, request):
        return Response({"rules": self.service.available_rules()})


class DetectFraudView(APIView):
    """Endpoint legado conservado para clientes existentes."""

    service = FraudDetectionService()

    def post(self, request):
        result = self.service.detect()
        requested_format = request.query_params.get("report") or request.query_params.get("format")
        if requested_format in ("text", "txt", "plain", "informe"):
            return HttpResponse(self._text_report(result), content_type="text/plain; charset=utf-8")
        return Response(result)

    def _text_report(self, result: dict) -> str:
        summary = result.get("summary", {})
        lines = [
            "REPORTE DE DETECCION DE FRAUDE",
            "================================",
            "",
            f"Fecha del analisis: {datetime.now().isoformat(timespec='seconds')}",
            f"Nivel de riesgo: {summary.get('risk_level', 'sin_datos')}",
            f"Alertas/evidencias: {summary.get('total_alerts', 0)}",
            f"Reglas activadas: {summary.get('rules_triggered', 0)}",
            "",
            "Detalle de reglas",
            "-----------------",
        ]
        for rule in result.get("rules", []):
            lines.append(f"- {rule.get('title', rule.get('rule'))}: {rule.get('count', 0)} caso(s)")
            for row in rule.get("results", [])[:3]:
                lines.append(f"  Evidencia: {row}")
        return "\n".join(lines)


class RunFraudDetectionView(DetectFraudView):
    """Endpoint JSON principal para la UI nueva."""

    def post(self, request):
        return Response(self.service.detect())
