"""Vistas de tablero, agregaciones, snapshot y consultas demo."""

from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.analytics_service import AnalyticsService


class DashboardView(APIView):
    def get(self, request):
        service = AnalyticsService()
        return Response(service.dashboard())


class AggregationView(APIView):
    def get(self, request):
        service = AnalyticsService()
        return Response(service.aggregations())


class DemoQueriesView(APIView):
    def get(self, request):
        service = AnalyticsService()
        return Response(service.demo_queries())


class GraphSnapshotView(APIView):
    def get(self, request):
        service = AnalyticsService()
        return Response(service.graph_snapshot())
