"""
Licencias, vistas
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
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.licencias.models import Licencia

MODULO = "LICENCIAS"

licencias = Blueprint("licencias", __name__, template_folder="templates")


@licencias.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@licencias.route("/licencias/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Licencias"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Licencia.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "tipo" in request.form:
        consulta = consulta.filter_by(tipo=request.form["tipo"])
    # Luego filtrar por columnas de otras tablas
    if "persona_nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["persona_nombre_completo"])
        if nombre_completo != "":
            consulta = consulta.join(Persona)
            consulta = consulta.filter(
                or_(
                    Persona.nombres.contains(nombre_completo),
                    Persona.apellido_primero.contains(nombre_completo),
                    Persona.apellido_segundo.contains(nombre_completo),
                )
            )
    # Ordenar y paginar
    registros = consulta.order_by(Licencia.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "periodo": resultado.fecha_inicio.strftime("%Y-%m-%d")
                    + " — "
                    + resultado.fecha_termino.strftime("%Y-%m-%d"),
                    "url": url_for("licencias.detail", licencia_id=resultado.id),
                },
                "tipo": resultado.tipo,
                "dias": f"{(resultado.fecha_termino - resultado.fecha_inicio).days + 1} DÍAS",
                "persona": resultado.persona.nombre_completo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@licencias.route("/licencias")
def list_active():
    """Listado de Licencias activos"""
    return render_template(
        "licencias/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Licencias",
        tipos=Licencia.TIPOS,
        estatus="A",
    )


@licencias.route("/licencias/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Licencias inactivas"""
    return render_template(
        "licencias/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Licencias inactivas",
        tipos=Licencia.TIPOS,
        estatus="B",
    )


@licencias.route("/licencias/<int:licencia_id>")
def detail(licencia_id):
    """Detalle de una Licencia"""
    licencia = Licencia.query.get_or_404(licencia_id)
    return render_template("licencias/detail.jinja2", licencia=licencia)
