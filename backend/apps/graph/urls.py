"""Rutas específicas de la API de grafo."""

from django.urls import path

from .views.analytics_views import AggregationView, DashboardView, DemoQueriesView, GraphSnapshotView
from .views.fraud_views import DetectFraudView, FraudRulesView
from .views.gds_views import (
    GDSDropView,
    GDSExecutionView,
    GDSExistsView,
    GDSLouvainView,
    GDSPagerankView,
    GDSProjectView,
    GDSSimilarityView,
    GDSShortestPathView,
)
from .views.ingestion_views import CSVUploadView, FakeDataGenerationView, SchemaBootstrapView
from .views.node_views import (
    DynamicLabelView,
    NodeDeleteBatchView,
    NodeDetailView,
    NodeListView,
    NodePropertyBatchView,
    NodePropertyView,
)
from .views.relationship_views import (
    RelationshipDeleteBatchView,
    RelationshipDetailView,
    RelationshipListView,
    RelationshipPropertyBatchView,
    RelationshipPropertyView,
)


urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("schema/bootstrap/", SchemaBootstrapView.as_view(), name="schema-bootstrap"),
    path("nodes/", NodeListView.as_view(), name="node-list"),
    path("nodes/<str:label>/<str:node_id>/", NodeDetailView.as_view(), name="node-detail"),
    path("nodes/<str:label>/<str:node_id>/properties/<str:property_name>/", NodePropertyView.as_view(), name="node-property"),
    path("nodes/properties/batch/", NodePropertyBatchView.as_view(), name="node-property-batch"),
    path("nodes/delete/", NodeDeleteBatchView.as_view(), name="node-bulk-delete"),
    path("nodes/<str:label>/<str:node_id>/labels/", DynamicLabelView.as_view(), name="dynamic-labels"),
    path("relationships/", RelationshipListView.as_view(), name="relationship-list"),
    path("relationships/<str:relationship_id>/", RelationshipDetailView.as_view(), name="relationship-detail"),
    path("relationships/<str:relationship_id>/properties/<str:property_name>/", RelationshipPropertyView.as_view(), name="relationship-property"),
    path("relationships/properties/batch/", RelationshipPropertyBatchView.as_view(), name="relationship-property-batch"),
    path("relationships/delete/", RelationshipDeleteBatchView.as_view(), name="relationship-bulk-delete"),
    path("upload/csv/", CSVUploadView.as_view(), name="csv-upload"),
    path("generate/fake-data/", FakeDataGenerationView.as_view(), name="fake-data"),
    path("fraud/rules/", FraudRulesView.as_view(), name="fraud-rules"),
    path("fraud/detect/", DetectFraudView.as_view(), name="fraud-detect"),
    path("analytics/aggregations/", AggregationView.as_view(), name="aggregations"),
    path("analytics/demo-queries/", DemoQueriesView.as_view(), name="demo-queries"),
    path("analytics/graph-snapshot/", GraphSnapshotView.as_view(), name="graph-snapshot"),
    path("gds/project/", GDSProjectView.as_view(), name="gds-project"),
    path("gds/exists/", GDSExistsView.as_view(), name="gds-exists"),
    path("gds/drop/", GDSDropView.as_view(), name="gds-drop"),
    path("gds/pagerank/", GDSPagerankView.as_view(), name="gds-pagerank"),
    path("gds/louvain/", GDSLouvainView.as_view(), name="gds-louvain"),
    path("gds/similarity/", GDSSimilarityView.as_view(), name="gds-similarity"),
    path("gds/shortest-path/", GDSShortestPathView.as_view(), name="gds-shortest-path"),
    path("gds/run/", GDSExecutionView.as_view(), name="gds-run"),
]
