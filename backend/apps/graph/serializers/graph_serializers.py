"""Serializadores DRF para validar payloads del grafo."""

from rest_framework import serializers


class NodeSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    properties = serializers.DictField()


class NodePropertySerializer(serializers.Serializer):
    value = serializers.JSONField(required=False)


class DynamicLabelSerializer(serializers.Serializer):
    label = serializers.CharField()
    action = serializers.ChoiceField(choices=["add", "remove"])


class RelationshipSerializer(serializers.Serializer):
    relationship_type = serializers.CharField()
    start_label = serializers.CharField()
    start_node_id = serializers.CharField()
    end_label = serializers.CharField()
    end_node_id = serializers.CharField()
    properties = serializers.DictField()


class RelationshipPropertySerializer(serializers.Serializer):
    value = serializers.JSONField(required=False)


class CSVUploadSerializer(serializers.Serializer):
    entity_type = serializers.CharField()
    file = serializers.FileField()


class FakeDataSerializer(serializers.Serializer):
    total_clientes = serializers.IntegerField(min_value=100, default=1000)
    cuentas_por_cliente = serializers.IntegerField(min_value=1, max_value=3, default=1)
    transacciones_por_cuenta = serializers.IntegerField(min_value=1, max_value=8, default=4)


class GDSExecutionSerializer(serializers.Serializer):
    algorithm = serializers.ChoiceField(choices=["pagerank", "louvain", "node_similarity", "shortest_path"])
    source_id = serializers.CharField(required=False)
    target_id = serializers.CharField(required=False)


class GDSShortestPathSerializer(serializers.Serializer):
    """
    Valida el payload del algoritmo de ruta más corta.

    Se separa del serializador genérico para dejar cada endpoint con una
    responsabilidad clara y facilitar mensajes de error más precisos.
    """

    source_id = serializers.CharField()
    target_id = serializers.CharField()
