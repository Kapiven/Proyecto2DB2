"""Vistas de reglas y ejecución de detección de fraude."""

from datetime import datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from ..services.fraud_service import FraudDetectionService


class FraudRulesView(APIView):
    service = FraudDetectionService()

    def get(self, request):
        return Response({"rules": self.service.available_rules()})


class DetectFraudView(APIView):
    service = FraudDetectionService()

    def post(self, request):
        detection_results = self.service.detect()
        
        # Calcular nivel de riesgo general
        total_alertas = detection_results.get("total_alertas", 0)
        if total_alertas == 0:
            riesgo_general = "BAJO - Sin alertas"
            color = "verde"
            icono_estado = "🟢"
        elif total_alertas <= 2:
            riesgo_general = "MEDIO - Revisar"
            color = "amarillo"
            icono_estado = "🟡"
        else:
            riesgo_general = "ALTO - Accion inmediata"
            color = "rojo"
            icono_estado = "🔴"
        
        report_payload = self._build_report_payload(
            detection_results, riesgo_general, total_alertas
        )

        requested_format = request.query_params.get("report") or request.query_params.get("format")
        if requested_format in ("text", "txt", "plain", "informe"):
            text_report = self._generate_text_report(report_payload)
            return HttpResponse(text_report, content_type="text/plain; charset=utf-8")

        # Si solicitan JSON, incluir tambien una version legible del informe.
        if requested_format == "json":
            return Response({
                "informe": self._generate_text_report(report_payload),
                **report_payload,
            })
        
        # Por defecto: devolver HTML legible
        html = self._generate_html_report(
            detection_results, riesgo_general, total_alertas, icono_estado
        )
        return HttpResponse(html, content_type='text/html; charset=utf-8')

    def _build_report_payload(self, detection_results, estado_general, total_alertas):
        """Normaliza los resultados para generar JSON, texto o HTML."""
        return {
            "reporte": {
                "titulo": "REPORTE DE DETECCION DE FRAUDE",
                "fecha_analisis": datetime.now().isoformat(),
                "estado_general": estado_general,
                "total_alertas_detectadas": total_alertas
            },
            "resumen": detection_results.get("resumen", "Sin alertas"),
            "detalle_reglas": {
                "Transacciones Rapidas (Burst)": {
                    "casos": detection_results["transacciones_rapidas"]["cantidad_detectadas"],
                    "definicion": detection_results["transacciones_rapidas"]["descripcion"],
                    "que_significa": "Multiples movimientos de dinero en muy poco tiempo podria indicar fraude automatizado o lavado de dinero",
                    "riesgo": detection_results["transacciones_rapidas"]["riesgo"]
                },
                "Cambios Sospechosos de Ubicacion": {
                    "casos": detection_results["cambio_ubicacion"]["cantidad_detectadas"],
                    "definicion": detection_results["cambio_ubicacion"]["descripcion"],
                    "que_significa": "Una persona no puede estar en dos paises en 30 minutos. Si sucede, la tarjeta podria estar siendo usada fraudulentamente",
                    "riesgo": detection_results["cambio_ubicacion"]["riesgo"]
                },
                "Dispositivos Compartidos": {
                    "casos": detection_results["dispositivo_compartido"]["cantidad_detectadas"],
                    "definicion": detection_results["dispositivo_compartido"]["descripcion"],
                    "que_significa": "El mismo dispositivo utilizado por multiples clientes es inusual y puede indicar actividad fraudulenta coordinada",
                    "riesgo": detection_results["dispositivo_compartido"]["riesgo"]
                },
                "Comercios de Alto Riesgo": {
                    "casos": detection_results["comercio_alto_riesgo"]["cantidad_detectadas"],
                    "definicion": detection_results["comercio_alto_riesgo"]["descripcion"],
                    "que_significa": "Transacciones en establecimientos conocidos por alto riesgo de fraude (casinos online, cripto, etc)",
                    "riesgo": detection_results["comercio_alto_riesgo"]["riesgo"]
                }
            },
            "recomendaciones": self._get_recommendations(detection_results),
            "proximos_pasos": self._get_next_steps(total_alertas)
        }

    def _generate_text_report(self, report_payload):
        """Genera un informe de texto plano para lectura humana."""
        reporte = report_payload["reporte"]
        fecha = datetime.fromisoformat(reporte["fecha_analisis"]).strftime("%d/%m/%Y %H:%M")

        lines = [
            reporte["titulo"],
            "=" * len(reporte["titulo"]),
            "",
            f"Fecha del analisis: {fecha}",
            f"Estado general: {reporte['estado_general']}",
            f"Alertas detectadas: {reporte['total_alertas_detectadas']}",
            "",
            "Resumen ejecutivo",
            "-----------------"
        ]

        resumen = report_payload.get("resumen") or "Sin alertas"
        for item in resumen.splitlines():
            item = item.strip()
            if item:
                lines.append(f"- {item}")

        lines.extend(["", "Detalle de reglas", "-----------------"])
        for rule_name, rule_info in report_payload["detalle_reglas"].items():
            lines.extend([
                f"- {rule_name}",
                f"  Casos detectados: {rule_info['casos']}",
                f"  Riesgo: {rule_info['riesgo']}",
                f"  Regla: {rule_info['definicion']}",
                f"  Interpretacion: {rule_info['que_significa']}"
            ])

        lines.extend(["", "Recomendaciones", "----------------"])
        for recommendation in report_payload["recomendaciones"]:
            lines.append(f"- {recommendation}")

        lines.extend(["", "Proximos pasos", "--------------"])
        for index, step in enumerate(report_payload["proximos_pasos"], 1):
            lines.append(f"{index}. {step}")

        return "\n".join(lines)
    
    def _get_recommendations(self, results):
        """Genera recomendaciones basadas en los resultados."""
        recommendations = []
        
        if results["transacciones_rapidas"]["cantidad_detectadas"] > 0:
            recommendations.append("CONTACTAR CLIENTE: Verificar si las transacciones rapidas son legitimas")
        
        if results["cambio_ubicacion"]["cantidad_detectadas"] > 0:
            recommendations.append("BLOQUEAR TEMPORALMENTE: Posible clonacion de tarjeta - cambio imposible de ubicacion")
        
        if results["dispositivo_compartido"]["cantidad_detectadas"] > 0:
            recommendations.append("REVISAR CUENTA: Un dispositivo compartido por multiples clientes es sospechoso")
        
        if results["comercio_alto_riesgo"]["cantidad_detectadas"] > 0:
            recommendations.append("MONITOREAR: Transacciones en comercios de alto riesgo requieren atencion")
        
        return recommendations if recommendations else ["CONTINUAR MONITOREANDO: Todo en orden por ahora"]
    
    def _get_next_steps(self, total_alertas):
        """Define los siguientes pasos segun el numero de alertas."""
        if total_alertas == 0:
            return [
                "Revisar en 1 hora",
                "Mantener monitoreo continuo",
                "Analizar tendencias semanales"
            ]
        elif total_alertas <= 2:
            return [
                "Contactar cliente para verificacion",
                "Revisar historial de transacciones",
                "Escalona a equipo de fraude si es necesario"
            ]
        else:
            return [
                "ACCION INMEDIATA: Bloquear cuenta",
                "Contactar cliente de inmediato",
                "Escalar a equipo de seguridad",
                "Reportar a autoridades si aplica"
            ]
    
    def _generate_html_report(self, detection_results, estado_general, total_alertas, icono):
        """Genera un reporte HTML legible sin código."""
        recommendations = self._get_recommendations(detection_results)
        next_steps = self._get_next_steps(total_alertas)
        
        fecha = datetime.now().strftime("%d de %B de %Y a las %H:%M")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte de Detección de Fraude</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; min-height: 100vh; }}
                .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                .header h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
                .header p {{ opacity: 0.9; font-size: 1em; }}
                .status {{ padding: 30px; text-align: center; border-bottom: 2px solid #f0f0f0; }}
                .status .state {{ font-size: 3em; margin-bottom: 10px; }}
                .status h2 {{ font-size: 1.8em; color: #333; margin-bottom: 5px; }}
                .status .alerts {{ font-size: 2em; font-weight: bold; color: #667eea; }}
                .section {{ padding: 30px; border-bottom: 1px solid #f0f0f0; }}
                .section h3 {{ color: #333; margin-bottom: 20px; font-size: 1.4em; display: flex; align-items: center; gap: 10px; }}
                .rule-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }}
                .rule-card {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; }}
                .rule-card.low {{ border-left: 4px solid #28a745; }}
                .rule-card.medium {{ border-left: 4px solid #ffc107; }}
                .rule-card.high {{ border-left: 4px solid #dc3545; }}
                .rule-card .count {{ font-size: 2.5em; font-weight: bold; color: #667eea; margin: 10px 0; }}
                .rule-card .name {{ font-weight: 600; color: #333; margin-bottom: 10px; }}
                .rule-card .risk {{ display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; margin-top: 10px; }}
                .rule-card .risk.low {{ background: #d4edda; color: #155724; }}
                .rule-card .risk.medium {{ background: #fff3cd; color: #856404; }}
                .rule-card .risk.high {{ background: #f8d7da; color: #721c24; }}
                .alert-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px; }}
                .alert-box::before {{ content: "⚠️ "; font-size: 1.2em; margin-right: 10px; }}
                .recommendation {{ background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 10px 0; border-radius: 4px; color: #1565c0; }}
                .recommendation::before {{ content: "→ "; font-weight: bold; margin-right: 10px; }}
                .step {{ display: flex; align-items: flex-start; margin: 15px 0; }}
                .step-number {{ background: #667eea; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; flex-shrink: 0; }}
                .step-text {{ color: #333; line-height: 1.6; padding-top: 5px; }}
                .footer {{ padding: 20px 30px; background: #f8f9fa; text-align: center; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 REPORTE DE DETECCIÓN DE FRAUDE</h1>
                    <p>Análisis realizado: {fecha}</p>
                </div>
                
                <div class="status">
                    <div class="state">{icono}</div>
                    <h2>Estado: {estado_general}</h2>
                    <div class="alerts">
                        <strong>{total_alertas} alertas detectadas</strong>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📊 Resumen Ejecutivo</h3>
                    <p style="font-size: 1.1em; line-height: 1.8; color: #555;">
                        {detection_results.get('resumen', 'Sin alertas').replace(chr(10), '<br>')}
                    </p>
                </div>
                
                <div class="section">
                    <h3>🔍 Análisis Detallado de Reglas</h3>
                    <div class="rule-grid">
        """
        
        # Agregar tarjetas de reglas
        rules_data = [
            ("Transacciones Rápidas", detection_results["transacciones_rapidas"]),
            ("Cambios de Ubicación", detection_results["cambio_ubicacion"]),
            ("Dispositivos Compartidos", detection_results["dispositivo_compartido"]),
            ("Comercios de Alto Riesgo", detection_results["comercio_alto_riesgo"])
        ]
        
        for rule_name, rule_info in rules_data:
            cases = rule_info["cantidad_detectadas"]
            risk = rule_info["riesgo"].lower()
            html += f"""
                        <div class="rule-card {risk}">
                            <div class="name">{rule_name}</div>
                            <div class="count">{cases}</div>
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 10px;">
                                {rule_info['descripcion']}
                            </div>
                            <span class="risk {risk}">{rule_info['riesgo']}</span>
                        </div>
            """
        
        html += """
                    </div>
                </div>
        """
        
        # Alertas
        if total_alertas > 0:
            html += """
                <div class="section">
                    <h3>⚠️ Alertas Detectadas</h3>
            """
            if detection_results["transacciones_rapidas"]["cantidad_detectadas"] > 0:
                html += f"<div class='alert-box'>{detection_results['transacciones_rapidas']['cantidad_detectadas']} transacción(es) rápida(s) detectada(s)</div>"
            if detection_results["cambio_ubicacion"]["cantidad_detectadas"] > 0:
                html += f"<div class='alert-box'>{detection_results['cambio_ubicacion']['cantidad_detectadas']} cambio(s) de ubicación sospechoso(s)</div>"
            if detection_results["dispositivo_compartido"]["cantidad_detectadas"] > 0:
                html += f"<div class='alert-box'>{detection_results['dispositivo_compartido']['cantidad_detectadas']} dispositivo(s) compartido(s) detectado(s)</div>"
            if detection_results["comercio_alto_riesgo"]["cantidad_detectadas"] > 0:
                html += f"<div class='alert-box'>{detection_results['comercio_alto_riesgo']['cantidad_detectadas']} transacción(es) en comercio(s) de alto riesgo</div>"
            html += """
                </div>
            """
        
        # Recomendaciones
        html += """
            <div class="section">
                <h3>💡 Recomendaciones</h3>
        """
        for rec in recommendations:
            html += f"<div class='recommendation'>{rec}</div>"
        html += """
            </div>
        """
        
        # Próximos pasos
        html += """
            <div class="section">
                <h3>📌 Próximos Pasos</h3>
        """
        for idx, step in enumerate(next_steps, 1):
            html += f"""
                <div class="step">
                    <div class="step-number">{idx}</div>
                    <div class="step-text">{step}</div>
                </div>
            """
        html += """
            </div>
        """
        
        html += """
                <div class="footer">
                    <strong>Sistema de Detección Heurística de Fraude</strong> | Análisis automático basado en 4 reglas
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
