"""
Vistas especializadas para Graph Data Science.

Cada endpoint delega toda la lógica al servicio GDS para mantener una
separación clara entre capa HTTP y lógica de negocio.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.graph_serializers import GDSExecutionSerializer, GDSShortestPathSerializer
from ..services.gds_service import GDSService


class GDSBaseView(APIView):
    """Base común para compartir la instancia del servicio."""

    def get_service(self):
        return GDSService()

    def handle_service_error(self, exc: Exception):
        """
        Convierte errores internos de GDS en JSON consistente.

        Esto ayuda al frontend a mostrar mensajes claros sin depender de
        trazas o errores HTML del servidor.
        """
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )


class GDSProjectView(GDSBaseView):
    """Crea la proyección `fraudGraph` solo si no existe."""

    def post(self, request):
        try:
            return Response(self.get_service().project_graph())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSExistsView(GDSBaseView):
    """Informa si `fraudGraph` ya existe en memoria."""

    def post(self, request):
        try:
            return Response(self.get_service().graph_exists())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSDropView(GDSBaseView):
    """Elimina la proyección GDS actual."""

    def delete(self, request):
        try:
            return Response(self.get_service().drop_graph())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSPagerankView(GDSBaseView):
    """Ejecuta PageRank y devuelve los nodos con mayor relevancia."""

    def post(self, request):
        try:
            return Response(self.get_service().page_rank())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSLouvainView(GDSBaseView):
    """Ejecuta Louvain y devuelve comunidades detectadas."""

    def post(self, request):
        try:
            return Response(self.get_service().louvain())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSSimilarityView(GDSBaseView):
    """Ejecuta Node Similarity y devuelve los pares más parecidos."""

    def post(self, request):
        try:
            return Response(self.get_service().node_similarity())
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSShortestPathView(GDSBaseView):
    """Ejecuta Dijkstra entre dos clientes y devuelve costo/ruta."""

    def post(self, request):
        serializer = GDSShortestPathSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(self.get_service().shortest_path(**serializer.validated_data))
        except Exception as exc:
            return self.handle_service_error(exc)


class GDSExecutionView(GDSBaseView):
    """
    Endpoint genérico legado.

    Se conserva para no romper funcionalidad existente, pero internamente
    delega al mismo servicio que usan los endpoints dedicados.
    """

    def post(self, request):
        serializer = GDSExecutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(self.get_service().run(**serializer.validated_data))
        except Exception as exc:
            return self.handle_service_error(exc)
