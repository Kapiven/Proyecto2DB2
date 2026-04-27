from django.urls import path
from .views import fraude_view, relacion_cliente_cuenta_view, relacion_cuenta_transaccion_view, test_neo4j, clientes_view, cliente_detail_view, cuentas_view, transacciones_view

urlpatterns = [
    path('test-neo4j/', test_neo4j),
    path('clientes/', clientes_view),
    path("clientes/<str:cliente_id>/", cliente_detail_view),
    path('cuentas/', cuentas_view),
    path('relacion-cliente-cuenta/', relacion_cliente_cuenta_view),
    path("transacciones/", transacciones_view),
    path("relacion-cuenta-transaccion/", relacion_cuenta_transaccion_view),
    path("fraude/", fraude_view)
]

