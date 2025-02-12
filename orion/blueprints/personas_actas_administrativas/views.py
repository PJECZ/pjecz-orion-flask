"""
Persona Actas Administrativas, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.personas_actas_administrativas.models import PersonaActaAdministrativa
from orion.blueprints.personas.models import Persona

MODULO = "PERSONAS ACTAS ADMINISTRATIVAS"

personas_actas_administrativas = Blueprint("personas_actas_administrativas", __name__, template_folder="templates")


@personas_actas_administrativas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_actas_administrativas.route("/personas_actas_administrativas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Personas Acta Administrativa"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PersonaActaAdministrativa.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(PersonaActaAdministrativa.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(PersonaActaAdministrativa.estatus == "A")
    if "id" in request.form:
        consulta = consulta.filter(PersonaActaAdministrativa.id == request.form["id"])
    # Luego filtrar por columnas de otras tablas
    if "persona_nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["persona_nombre_completo"])
        if nombre_completo != "":
            consulta = consulta.join(Persona)
            for palabra in nombre_completo.split(" "):
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    if "persona_id" in request.form:
        consulta = consulta.join(Persona)
        consulta = consulta.filter(Persona.id == request.form["persona_id"])
    # Ordenar y paginar
    registros = consulta.order_by(PersonaActaAdministrativa.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=resultado.id),
                },
                "persona": {
                    "nombre": resultado.persona.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.persona.id),
                },
                "fecha": resultado.fecha.strftime("%Y-%m-%d"),
                "falta": resultado.falta,
                "sancion": resultado.sancion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas_actas_administrativas.route("/personas_actas_administrativas")
def list_active():
    """Listado de Actas Administrativas activos"""
    return render_template(
        "personas_actas_administrativas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Actas Administrativas",
        estatus="A",
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Actas Administrativas inactivos"""
    return render_template(
        "personas_actas_administrativas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Actas Administrativas inactivos",
        estatus="B",
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/<int:persona_acta_administrativa_id>")
def detail(persona_acta_administrativa_id):
    """Detalle de un Persona Acta Administrativa"""
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)
    return render_template(
        "personas_actas_administrativas/detail.jinja2", persona_acta_administrativa=persona_acta_administrativa
    )
