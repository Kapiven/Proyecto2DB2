from .neo4j_driver import get_driver


def create_cliente(data):
    driver = get_driver()

    query = """
    CREATE (c:Cliente {
        id: $id,
        nombre: $nombre,
        edad: $edad,
        genero: $genero,
        email: $email,
        telefono: $telefono,
        riesgo: $riesgo,
        nivel_riesgo: $nivel_riesgo,
        fecha_registro: $fecha_registro
    })
    RETURN c
    """

    with driver.session() as session:
        result = session.run(query, data)
        record = result.single()

    return dict(record["c"])


def get_clientes():
    driver = get_driver()

    query = """
    MATCH (c:Cliente)
    RETURN c
    """

    clientes = []

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            clientes.append(dict(record["c"]))

    return clientes

def update_cliente(cliente_id, data):
    driver = get_driver()

    query = """
    MATCH (c:Cliente {id: $id})
    SET c.nombre = $nombre,
        c.edad = $edad,
        c.genero = $genero,
        c.email = $email,
        c.telefono = $telefono,
        c.riesgo = $riesgo,
        c.nivel_riesgo = $nivel_riesgo,
        c.fecha_registro = $fecha_registro
    RETURN c
    """

    params = {"id": cliente_id, **data}

    with driver.session() as session:
        result = session.run(query, params)
        record = result.single()

    return dict(record["c"])

def delete_cliente(cliente_id):
    driver = get_driver()

    query = """
    MATCH (c:Cliente {id: $id})
    DETACH DELETE c
    """

    with driver.session() as session:
        session.run(query, {"id": cliente_id})
        
# Cuentas
def create_cuenta(data):
    driver = get_driver()

    query = """
    CREATE (cu:Cuenta {
        id: $id,
        saldo: $saldo,
        tipo: $tipo,
        estado: $estado,
        fecha_apertura: $fecha_apertura,
        limite_credito: $limite_credito
    })
    RETURN cu
    """

    with driver.session() as session:
        result = session.run(query, data)
        record = result.single()

    return dict(record["cu"])


def get_cuentas():
    driver = get_driver()

    query = """
    MATCH (cu:Cuenta)
    RETURN cu
    """

    cuentas = []

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            cuentas.append(dict(record["cu"]))

    return cuentas

def relacionar_cliente_cuenta(cliente_id, cuenta_id):
    driver = get_driver()

    query = """
    MATCH (c:Cliente {id: $cliente_id})
    MATCH (cu:Cuenta {id: $cuenta_id})

    CREATE (c)-[:TIENE {
        fecha_asignacion: date(),
        estado: "activa",
        prioridad: 1
    }]->(cu)

    RETURN c, cu
    """

    with driver.session() as session:
        result = session.run(query, {
            "cliente_id": cliente_id,
            "cuenta_id": cuenta_id
        })

        return result.single()
    
# Transacciones
def create_transaccion(data):
    driver = get_driver()

    query = """
    CREATE (t:Transaccion {
        id: $id,
        monto: $monto,
        tipo: $tipo,
        fecha: $fecha,
        estado: $estado,
        fraudulenta: $fraudulenta,
        canal: $canal,
        razones_sospecha: $razones_sospecha,
        comercio: $comercio,
        ubicacion: $ubicacion
    })
    RETURN t
    """

    with driver.session() as session:
        result = session.run(query, data)
        record = result.single()

    return dict(record["t"])


def get_transacciones():
    driver = get_driver()

    query = """
    MATCH (t:Transaccion)
    RETURN t
    """

    transacciones = []

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            transacciones.append(dict(record["t"]))

    return transacciones

# Relacionar cuenta con transacción
def relacionar_cuenta_transaccion(cuenta_id, transaccion_id):
    driver = get_driver()

    query = """
    MATCH (cu:Cuenta {id: $cuenta_id})
    MATCH (t:Transaccion {id: $transaccion_id})

    CREATE (cu)-[:REALIZA {
        fecha: date(),
        canal: "web",
        saldo_antes: cu.saldo,
        saldo_despues: cu.saldo + t.monto
    }]->(t)

    RETURN cu, t
    """

    with driver.session() as session:
        return session.run(query, {
            "cuenta_id": cuenta_id,
            "transaccion_id": transaccion_id
        }).single()
        
# Detección de fraude: transacciones con monto alto
def detectar_fraude_montos_altos():
    driver = get_driver()

    query = """
    MATCH (t:Transaccion)
    WHERE t.monto > 10000
    RETURN t
    """

    sospechosas = []

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            sospechosas.append(dict(record["t"]))

    return sospechosas