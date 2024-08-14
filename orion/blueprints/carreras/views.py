"""
Carreras, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.carreras.models import Carrera
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required

MODULO = "CARRERAS"

carreras = Blueprint("carreras", __name__, template_folder="templates")


@carreras.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@carreras.route("/carreras/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Carreras"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Carrera.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Carrera.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Carrera.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("carreras.detail", carrera_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@carreras.route("/carreras")
def list_active():
    """Listado de Carreras activos"""
    return render_template(
        "carreras/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Carreras",
        estatus="A",
    )


@carreras.route("/carreras/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Carreras inactivos"""
    return render_template(
        "carreras/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Carreras inactivos",
        estatus="B",
    )


@carreras.route("/carreras/<int:carrera_id>")
def detail(carrera_id):
    """Detalle de un Carrera"""
    carrera = Carrera.query.get_or_404(carrera_id)
    return render_template("carreras/detail.jinja2", carrera=carrera)
