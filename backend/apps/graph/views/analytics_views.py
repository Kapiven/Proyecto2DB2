"""Vistas de tablero, agregaciones, snapshot y consultas demo."""

from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.analytics_service import AnalyticsService


class DashboardView(APIView):
    service = AnalyticsService()

    def get(self, request):
        return Response(self.service.dashboard())


class AggregationView(APIView):
    service = AnalyticsService()

    def get(self, request):
        return Response(self.service.aggregations())


class DemoQueriesView(APIView):
    service = AnalyticsService()

    def get(self, request):
        return Response(self.service.demo_queries())


class GraphSnapshotView(APIView):
    service = AnalyticsService()

    def get(self, request):
        return Response(self.service.graph_snapshot())
