"""Servicios de carga y generación de datos."""

from __future__ import annotations

import csv
import io
import random
import re
from datetime import date, datetime, timedelta, timezone

from faker import Faker

from .neo4j_service import Neo4jRepository


class IngestionService:
    """Maneja la ingesta y generación masiva de información."""

    def __init__(self) -> None:
        self.repository = Neo4jRepository()
        self.faker = Faker("es_ES")

    def bootstrap_constraints(self):
        labels = ["Cliente", "Cuenta", "Tarjeta", "Transaccion", "Dispositivo", "Ubicacion", "Comercio", "Banco", "Alerta"]
        results = []
        for label in labels:
            query = f"CREATE INDEX {label.lower()}_id_index IF NOT EXISTS FOR (n:`{label}`) ON (n.id)"
            self.repository.execute_write(query)
            results.append({"label": label, "index": "ok"})
        return results

    def import_csv(self, entity_type: str, file_bytes: bytes):
        content = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        if entity_type in {"Cliente", "Cuenta", "Tarjeta", "Transaccion", "Dispositivo", "Ubicacion", "Comercio", "Banco", "Alerta"}:
            return self._import_nodes(entity_type, rows)
        return self._import_relationships(entity_type, rows)

    def _import_nodes(self, label: str, rows: list[dict]):
        normalized_rows = [self._normalize_row(row) for row in rows]
        query = f"""
            UNWIND $rows AS row
            MERGE (n:`{label}` {{id: row.id}})
            SET n += row
            RETURN count(*) AS processed
        """
        return self.repository.execute_write(query, {"rows": normalized_rows})[0]

    def _import_relationships(self, relationship_type: str, rows: list[dict]):
        normalized_rows = [self._normalize_row(row) for row in rows]
        prepared_rows = []
        for row in normalized_rows:
            properties = {key: value for key, value in row.items() if key not in {"start_id", "end_id"}}
            prepared_rows.append({"start_id": row["start_id"], "end_id": row["end_id"], "properties": properties})
        query = f"""
            UNWIND $rows AS row
            MATCH (a {{id: row.start_id}})
            MATCH (b {{id: row.end_id}})
            MERGE (a)-[r:`{relationship_type}`]->(b)
            SET r += row.properties
            RETURN count(*) AS processed
        """
        return self.repository.execute_write(query, {"rows": prepared_rows})[0]

    def generate_fake_data(self, total_clientes: int, cuentas_por_cliente: int, transacciones_por_cuenta: int):
        now = datetime.now(timezone.utc)
        bancos = [
            {
                "id": f"BAN-{index:03d}",
                "nombre": f"Banco {self.faker.company()}",
                "codigo": f"BC{index:03d}",
                "ciudad": self.faker.city(),
                "tipo": random.choice(["Tradicional", "Digital", "Cooperativa"]),
                "riesgo": random.randint(1, 10),
                "nivel_riesgo": random.choice(["Bajo", "Medio", "Alto"]),
            }
            for index in range(10)
        ]
        comercios = [
            {
                "id": f"COM-{index:04d}",
                "nombre": self.faker.company(),
                "categoria": random.choice(["Retail", "Viajes", "Gaming", "Electrónica", "Alimentos"]),
                "riesgo": random.randint(1, 10),
                "ciudad": self.faker.city(),
                "extra_labels": ["AltoRiesgo"] if random.random() < 0.2 else [],
            }
            for index in range(80)
        ]
        ubicaciones = [
            {
                "id": f"UBI-{index:04d}",
                "latitud": round(random.uniform(-55, 55), 6),
                "longitud": round(random.uniform(-120, 120), 6),
                "ciudad": self.faker.city(),
                "pais": random.choice(["Guatemala", "México", "Colombia", "España", "Chile"]),
                "direccion": self.faker.address().replace("\n", ", "),
            }
            for index in range(120)
        ]

        self._batch_create_nodes("Banco", bancos)
        self._batch_create_nodes("Comercio", comercios, allow_extra_labels=True)
        self._batch_create_nodes("Ubicacion", ubicaciones)

        clientes = []
        cuentas = []
        tarjetas = []
        dispositivos = []
        transacciones = []
        alertas = []
        rels = {key: [] for key in ["TIENE_CUENTA", "USA_DISPOSITIVO", "TIENE_TARJETA", "ORIGINA", "DESTINADA_A", "UTILIZA_DISPOSITIVO", "DESDE_UBICACION", "EN_COMERCIO", "UTILIZA_TARJETA", "GENERA_ALERTA", "PERTENECE_A", "LOCALIZADO_EN", "REMITE", "INTERACTUA"]}

        shared_device_ids = [f"DIS-SHARED-{idx}" for idx in range(25)]
        for shared_id in shared_device_ids:
            dispositivos.append(
                {
                    "id": shared_id,
                    "tipo": random.choice(["Móvil", "Laptop", "Tablet"]),
                    "ip_address": self.faker.ipv4_public(),
                    "user_agent": self.faker.user_agent(),
                    "ultima_conexion": now - timedelta(minutes=random.randint(1, 300)),
                }
            )

        for client_index in range(total_clientes):
            client_id = f"CLI-{client_index:05d}"
            risk_score = round(random.uniform(0.1, 0.98), 2)
            risk_level = "Alto" if risk_score >= 0.75 else "Medio" if risk_score >= 0.45 else "Bajo"
            extra_labels = ["AltoRiesgo"] if risk_level == "Alto" else [f"Riesgo{risk_level}"]
            clientes.append(
                {
                    "id": client_id,
                    "nombre": self.faker.name(),
                    "edad": random.randint(18, 78),
                    "genero": random.choice(["F", "M", "X"]),
                    "riesgo": risk_score,
                    "nivel_riesgo": risk_level,
                    "fecha_registro": (now - timedelta(days=random.randint(60, 1800))).date(),
                    "email": self.faker.email(),
                    "telefono": self.faker.phone_number(),
                    "extra_labels": extra_labels,
                }
            )
            client_device_ids = []
            for device_index in range(random.randint(1, 2)):
                if random.random() < 0.25:
                    device_id = random.choice(shared_device_ids)
                else:
                    device_id = f"DIS-{client_index:05d}-{device_index}"
                    dispositivos.append(
                        {
                            "id": device_id,
                            "tipo": random.choice(["Móvil", "Laptop", "Tablet"]),
                            "ip_address": self.faker.ipv4_public(),
                            "user_agent": self.faker.user_agent(),
                            "ultima_conexion": now - timedelta(minutes=random.randint(1, 600)),
                        }
                    )
                client_device_ids.append(device_id)
                rels["USA_DISPOSITIVO"].append({
                    "start_id": client_id,
                    "end_id": device_id,
                    "fecha_uso": now - timedelta(minutes=random.randint(1, 120)),
                    "primera_vez": random.choice([True, False]),
                    "veces_usado": random.randint(1, 120),
                })
                rels["LOCALIZADO_EN"].append({
                    "start_id": device_id,
                    "end_id": random.choice(ubicaciones)["id"],
                    "fecha": now - timedelta(minutes=random.randint(1, 120)),
                    "tipo_conexion": random.choice(["wifi", "datos", "vpn"]),
                    "ip_detectada": self.faker.ipv4_public(),
                })

            for account_index in range(cuentas_por_cliente):
                account_id = f"CUE-{client_index:05d}-{account_index}"
                cuentas.append(
                    {
                        "id": account_id,
                        "saldo": round(random.uniform(100, 45000), 2),
                        "tipo": random.choice(["Ahorro", "Corriente", "Crédito"]),
                        "estado": random.choice(["Activa", "Revisión", "Bloqueada"]),
                        "fecha_apertura": (now - timedelta(days=random.randint(10, 2000))).date(),
                        "limite_credito": round(random.uniform(1000, 25000), 2),
                        "extra_labels": ["Sospechosa"] if risk_level == "Alto" and random.random() < 0.1 else [],
                    }
                )
                rels["TIENE_CUENTA"].append({
                    "start_id": client_id,
                    "end_id": account_id,
                    "fecha_asignacion": now.date(),
                    "tipo_relacion": "Titular",
                    "es_principal": account_index == 0,
                })
                rels["PERTENECE_A"].append({
                    "start_id": account_id,
                    "end_id": random.choice(bancos)["id"],
                    "fecha_asociacion": now.date(),
                    "canal_apertura": random.choice(["Sucursal", "Web", "App"]),
                    "verificada": random.choice([True, False]),
                })

                tarjeta_id = f"TAR-{client_index:05d}-{account_index}"
                tarjetas.append(
                    {
                        "id": tarjeta_id,
                        "numero": self.faker.credit_card_number(),
                        "tipo": random.choice(["Débito", "Crédito", "Virtual"]),
                        "estado": random.choice(["Activa", "Suspendida", "Expirada"]),
                        "fecha_expiracion": (now + timedelta(days=random.randint(200, 1200))).date(),
                        "limite": round(random.uniform(1000, 25000), 2),
                    }
                )
                rels["TIENE_TARJETA"].append({
                    "start_id": account_id,
                    "end_id": tarjeta_id,
                    "fecha_emision": now.date(),
                    "es_principal": True,
                    "estado_asignacion": "Activa",
                })

                last_transaction_time = now - timedelta(days=random.randint(1, 40))
                for trx_index in range(transacciones_por_cuenta):
                    last_transaction_time += timedelta(
                        minutes=random.randint(1, 4) if trx_index > 0 and random.random() < 0.25 else random.randint(360, 1800)
                    )
                    transaction_id = f"TRX-{client_index:05d}-{account_index}-{trx_index}"
                    commerce = random.choice(comercios)
                    location = random.choice(ubicaciones)
                    device_id = random.choice(client_device_ids)
                    suspicious_reasons = []
                    if commerce["riesgo"] >= 8:
                        suspicious_reasons.append("comercio_alto_riesgo")
                    if device_id in shared_device_ids:
                        suspicious_reasons.append("dispositivo_compartido")
                    if random.random() < 0.15:
                        suspicious_reasons.append("ubicacion_distinta")
                    fraud_flag = len(suspicious_reasons) >= 2
                    monto = round(random.uniform(10, 4000), 2)
                    transacciones.append(
                        {
                            "id": transaction_id,
                            "monto": monto,
                            "fecha": last_transaction_time,
                            "tipo": random.choice(["Compra", "Retiro", "Transferencia"]),
                            "fraudulenta": fraud_flag,
                            "estado": random.choice(["Aprobada", "Pendiente", "Rechazada"]),
                            "canal": random.choice(["Web", "POS", "App", "ATM"]),
                            "razones_sospecha": suspicious_reasons,
                            "extra_labels": ["Fraudulenta"] if fraud_flag else ["Sospechosa"] if suspicious_reasons else [],
                        }
                    )
                    rels["ORIGINA"].append({
                        "start_id": account_id,
                        "end_id": transaction_id,
                        "fecha_origen": last_transaction_time,
                        "tipo_operacion": "cargo",
                        "es_inusual": bool(suspicious_reasons),
                    })
                    rels["DESTINADA_A"].append({
                        "start_id": account_id,
                        "end_id": transaction_id,
                        "fecha_destino": last_transaction_time,
                        "tipo_destino": random.choice(["propia", "tercero", "comercio"]),
                        "es_sospechosa": bool(suspicious_reasons),
                    })
                    rels["UTILIZA_DISPOSITIVO"].append({
                        "start_id": transaction_id,
                        "end_id": device_id,
                        "fecha": last_transaction_time,
                        "dispositivo_nuevo": random.choice([True, False]),
                        "coincidencia_usuario": device_id not in shared_device_ids,
                    })
                    rels["DESDE_UBICACION"].append({
                        "start_id": transaction_id,
                        "end_id": location["id"],
                        "distancia_km": round(random.uniform(0.1, 3000), 2),
                        "es_anomala": "ubicacion_distinta" in suspicious_reasons,
                        "cambio_pais": location["pais"] != "Guatemala",
                    })
                    rels["EN_COMERCIO"].append({
                        "start_id": transaction_id,
                        "end_id": commerce["id"],
                        "frecuencia_cliente": random.randint(1, 30),
                        "es_comercio_habitual": random.choice([True, False]),
                        "coincidencia_categoria": random.choice([True, False]),
                    })
                    rels["UTILIZA_TARJETA"].append({
                        "start_id": transaction_id,
                        "end_id": tarjeta_id,
                        "metodo_autenticacion": random.choice(["PIN", "OTP", "Biometría", "3DS"]),
                        "intento_fallido": random.randint(0, 3),
                        "tarjeta_nueva": random.choice([True, False]),
                    })

                    target_account_id = random.choice(cuentas)["id"] if cuentas else account_id
                    rels["REMITE"].append({
                        "start_id": transaction_id,
                        "end_id": target_account_id,
                        "monto_recibido": round(monto - random.uniform(0.0, min(20.0, monto * 0.05)), 2),
                        "fecha_recepcion": last_transaction_time + timedelta(minutes=random.randint(1, 120)),
                        "comision": round(random.uniform(0.0, 50.0), 2),
                    })
                    rels["INTERACTUA"].append({
                        "start_id": transaction_id,
                        "end_id": random.choice(bancos)["id"],
                        "tipo_transferencia": random.choice(["Nacional", "Internacional", "ACH", "SWIFT"]),
                        "codigo_swift": f"{random.choice(['ABC', 'DEF', 'GHI', 'JKL'])}{random.randint(1000, 9999)}",
                        "costo_transferencia": round(random.uniform(0.5, 30.0), 2),
                        "tiempo_procesamiento": random.randint(1, 120),
                    })
                    if fraud_flag or suspicious_reasons:
                        alert_id = f"ALT-{client_index:05d}-{account_index}-{trx_index}"
                        severity = "Alta" if fraud_flag else "Media"
                        alertas.append(
                            {
                                "id": alert_id,
                                "tipo_alerta": "Transacción sospechosa",
                                "fecha": last_transaction_time,
                                "severidad": severity,
                                "descripcion": ", ".join(suspicious_reasons) or "Regla heurística",
                                "resuelta": False,
                            }
                        )
                        rels["GENERA_ALERTA"].append(
                            {
                                "start_id": transaction_id,
                                "end_id": alert_id,
                                "score_riesgo": round(min(0.99, risk_score + len(suspicious_reasons) * 0.12), 2),
                                "regla_activada": suspicious_reasons[0] if suspicious_reasons else "heuristica",
                                "prioridad": severity,
                            }
                        )

        self._batch_create_nodes("Cliente", clientes, allow_extra_labels=True)
        self._batch_create_nodes("Cuenta", cuentas, allow_extra_labels=True)
        self._batch_create_nodes("Tarjeta", tarjetas)
        self._batch_create_nodes("Dispositivo", dispositivos)
        self._batch_create_nodes("Transaccion", transacciones, allow_extra_labels=True)
        self._batch_create_nodes("Alerta", alertas)
        for rel_type, rel_rows in rels.items():
            self._batch_create_relationships(rel_type, rel_rows)

        return {
            "clientes": len(clientes),
            "cuentas": len(cuentas),
            "tarjetas": len(tarjetas),
            "dispositivos": len(dispositivos),
            "transacciones": len(transacciones),
            "alertas": len(alertas),
            "bancos": len(bancos),
            "comercios": len(comercios),
            "ubicaciones": len(ubicaciones),
            "total_nodos": len(clientes) + len(cuentas) + len(tarjetas) + len(dispositivos) + len(transacciones) + len(alertas) + len(bancos) + len(comercios) + len(ubicaciones),
        }

    def _batch_create_nodes(self, label: str, rows: list[dict], allow_extra_labels: bool = False):
        batch_rows = []
        for row in rows:
            payload = dict(row)
            extra_labels = payload.pop("extra_labels", [])
            batch_rows.append({"properties": payload, "extra_labels": extra_labels})
        query = f"""
            UNWIND $rows AS row
            MERGE (n:`{label}` {{id: row.properties.id}})
            SET n += row.properties
            RETURN count(*) AS processed
        """
        self.repository.execute_write(query, {"rows": batch_rows})
        if allow_extra_labels:
            for row in batch_rows:
                for extra_label in row["extra_labels"]:
                    self.repository.execute_write(f"MATCH (n:`{label}` {{id: $node_id}}) SET n:`{extra_label}`", {"node_id": row["properties"]["id"]})

    def _batch_create_relationships(self, relationship_type: str, rows: list[dict]):
        prepared = []
        for row in rows:
            payload = dict(row)
            start_id = payload.pop("start_id")
            end_id = payload.pop("end_id")
            prepared.append({"start_id": start_id, "end_id": end_id, "properties": payload})
        query = f"""
            UNWIND $rows AS row
            MATCH (a {{id: row.start_id}})
            MATCH (b {{id: row.end_id}})
            MERGE (a)-[r:`{relationship_type}`]->(b)
            SET r += row.properties
            RETURN count(*) AS processed
        """
        self.repository.execute_write(query, {"rows": prepared})

    def _normalize_row(self, row: dict):
        normalized = {}
        for key, value in row.items():
            if value is None:
                normalized[key] = None
                continue
            value = value.strip()
            if value == "":
                normalized[key] = None
                continue
            if value.lower() in {"true", "false"}:
                normalized[key] = value.lower() == "true"
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if not inner:
                    normalized[key] = []
                else:
                    items = re.split(r"\s*\|\s*|\s*,\s*", inner)
                    normalized[key] = [self._normalize_row({"item": item})["item"] for item in items if item.strip()]
                continue
            if re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", value):
                try:
                    normalized[key] = datetime.fromisoformat(value)
                    continue
                except ValueError:
                    pass
            if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                try:
                    normalized[key] = date.fromisoformat(value)
                    continue
                except ValueError:
                    pass
            try:
                normalized[key] = int(value)
                continue
            except ValueError:
                pass
            try:
                normalized[key] = float(value)
                continue
            except ValueError:
                pass
            normalized[key] = value
        return normalized
