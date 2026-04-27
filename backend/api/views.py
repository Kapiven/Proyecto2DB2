from django.http import JsonResponse
from .neo4j_driver import get_driver
from django.views.decorators.csrf import csrf_exempt
from .services import create_cliente, detectar_fraude_montos_altos, get_clientes, update_cliente, delete_cliente
from .services import create_cuenta, get_cuentas
from .services import relacionar_cliente_cuenta, relacionar_cuenta_transaccion
from .services import create_transaccion, get_transacciones
import json

def test_neo4j(request):
    driver = get_driver()

    with driver.session() as session:
        result = session.run("RETURN 'Neo4j conectado' AS mensaje")
        record = result.single()

    return JsonResponse({
        "mensaje": record["mensaje"]
    })
    
@csrf_exempt
def clientes_view(request):
    if request.method == "GET":
        clientes = get_clientes()
        return JsonResponse(clientes, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)

        cliente = create_cliente(data)

        return JsonResponse({
            "mensaje": "Cliente creado",
            "cliente": cliente
        })
        
@csrf_exempt
def cliente_detail_view(request, cliente_id):
    if request.method == "PUT":
        data = json.loads(request.body)

        cliente = update_cliente(cliente_id, data)

        return JsonResponse({
            "mensaje": "Cliente actualizado",
            "cliente": cliente
        })

    elif request.method == "DELETE":
        delete_cliente(cliente_id)

        return JsonResponse({
            "mensaje": "Cliente eliminado"
        })
        
# Cuentas
@csrf_exempt
def cuentas_view(request):
    if request.method == "GET":
        cuentas = get_cuentas()
        return JsonResponse(cuentas, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)

        cuenta = create_cuenta(data)

        return JsonResponse({
            "mensaje": "Cuenta creada",
            "cuenta": cuenta
        })
        
# Relación Cliente-Cuenta
@csrf_exempt
def relacion_cliente_cuenta_view(request):
    if request.method == "POST":
        data = json.loads(request.body)

        relacionar_cliente_cuenta(
            data["cliente_id"],
            data["cuenta_id"]
        )

        return JsonResponse({
            "mensaje": "Relación creada"
        })
        
@csrf_exempt
def transacciones_view(request):
    if request.method == "GET":
        transacciones = get_transacciones()
        return JsonResponse(transacciones, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)

        transaccion = create_transaccion(data)

        return JsonResponse({
            "mensaje": "Transacción creada",
            "transaccion": transaccion
        })
        
# Relación Cuenta-Transacción
@csrf_exempt
def relacion_cuenta_transaccion_view(request):
    if request.method == "POST":
        data = json.loads(request.body)

        relacionar_cuenta_transaccion(
            data["cuenta_id"],
            data["transaccion_id"]
        )

        return JsonResponse({
            "mensaje": "Relación cuenta-transacción creada"
        })
        
def fraude_view(request):
    sospechosas = detectar_fraude_montos_altos()

    return JsonResponse({
        "transacciones_sospechosas": sospechosas
    })