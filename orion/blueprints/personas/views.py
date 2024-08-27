"""
Personas, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required

MODULO = "PERSONAS"

personas = Blueprint("personas", __name__, template_folder="templates")


@personas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas.route("/personas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Personas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Persona.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "numero_empleado" in request.form:
        try:
            numero_empleado = int(request.form["numero_empleado"])
            consulta = consulta.filter_by(numero_empleado=numero_empleado)
        except ValueError:
            pass
    if "nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["nombre_completo"])
        if nombre_completo != "":
            for palabra in nombre_completo.split(" "):
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    if "situacion" in request.form:
        consulta = consulta.filter_by(situacion=request.form["situacion"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(Persona.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "numero_empleado": resultado.numero_empleado,
                "detalle": {
                    "nombre_completo": resultado.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.id),
                },
                "situacion": {
                    "nombre": resultado.situacion,
                    "descripcion": Persona.SITUACIONES[resultado.situacion],
                },
                "sexo": "HOMBRE" if resultado.sexo == "H" else "MUJER",
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas.route("/personas")
def list_active():
    """Listado de Personas activos"""
    return render_template(
        "personas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Personas",
        situaciones=Persona.SITUACIONES,
        estatus="A",
    )


@personas.route("/personas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Personas inactivos"""
    return render_template(
        "personas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Personas inactivos",
        situaciones=Persona.SITUACIONES,
        estatus="B",
    )


@personas.route("/personas/<int:persona_id>")
def detail(persona_id):
    """Detalle de un Persona"""
    persona = Persona.query.get_or_404(persona_id)
    return render_template("personas/detail.jinja2", persona=persona)


@personas.route("/personas/query_personas_json", methods=["POST"])
def query_personas_json():
    """Proporcionar el JSON de Persona para elegir en un Select2"""
    consulta = Persona.query.filter_by(estatus="A")
    if "nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["nombre_completo"]).upper()
        if nombre_completo != "":
            palabras = nombre_completo.split()
            for palabra in palabras:
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    results = []
    for persona in consulta.order_by(Persona.id).limit(15).all():
        results.append(
            {
                "id": persona.id,
                "text": persona.nombre_completo,
            }
        )
    return {"results": results, "pagination": {"more": False}}
