"""
Centros de Trabajo, vistas
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
from orion.blueprints.centros_trabajos.models import CentroTrabajo

MODULO = "CENTROS TRABAJOS"

centros_trabajos = Blueprint("centros_trabajos", __name__, template_folder="templates")


@centros_trabajos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@centros_trabajos.route("/centros_trabajos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Centros de Trabajos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CentroTrabajo.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_string(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(CentroTrabajo.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(CentroTrabajo.nombre.contains(nombre))
    if "distrito_id" in request.form:
        consulta = consulta.filter_by(distrito_id=request.form["distrito_id"])
    if "organo_id" in request.form:
        consulta = consulta.filter_by(organo_id=request.form["organo_id"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(CentroTrabajo.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("centros_trabajos.detail", centro_trabajo_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@centros_trabajos.route("/centros_trabajos")
def list_active():
    """Listado de Centros de Trabajos activos"""
    return render_template(
        "centros_trabajos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Centros de Trabajos",
        estatus="A",
    )


@centros_trabajos.route("/centros_trabajos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Centros de Trabajos inactivos"""
    return render_template(
        "centros_trabajos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Centros de Trabajos inactivos",
        estatus="B",
    )


@centros_trabajos.route("/centros_trabajos/<int:centro_trabajo_id>")
def detail(centro_trabajo_id):
    """Detalle de un Centro de Trabajo"""
    centro_trabajo = CentroTrabajo.query.get_or_404(centro_trabajo_id)
    return render_template("centros_trabajos/detail.jinja2", centro_trabajo=centro_trabajo)


# NEW

# EDIT

# DELETE

# RECOVER


@centros_trabajos.route("/centros_trabajos/query_centros_trabajos_json", methods=["POST"])
def query_centros_trabajos_json():
    """Proporcionar el JSON de Centros de Trabajos para elegir en un Select2"""
    consulta = CentroTrabajo.query.filter_by(estatus="A")
    if "clave_nombre" in request.form:
        clave_nombre = safe_string(request.form["clave_nombre"]).upper()
        if clave_nombre != "":
            consulta = consulta.filter(
                or_(CentroTrabajo.clave.contains(clave_nombre), CentroTrabajo.nombre.contains(clave_nombre))
            )
    results = []
    for centro_trabajo in consulta.order_by(CentroTrabajo.id).limit(15).all():
        results.append(
            {
                "id": centro_trabajo.id,
                "text": centro_trabajo.clave_nombre,
            }
        )
    return {"results": results, "pagination": {"more": False}}
