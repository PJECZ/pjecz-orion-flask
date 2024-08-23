"""
Historial Puestos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.historial_puestos.forms import HistorialPuestoForm
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.historial_puestos.models import HistorialPuesto

MODULO = "HISTORIAL PUESTOS"

historial_puestos = Blueprint("historial_puestos", __name__, template_folder="templates")


@historial_puestos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@historial_puestos.route("/historial_puestos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Historial de Puestos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = HistorialPuesto.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(HistorialPuesto.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(HistorialPuesto.estatus == "A")
    # if "persona_id" in request.form:
    #     consulta = consulta.filter_by(persona_id=request.form["persona_id"])
    # Luego filtrar por columnas de otras tablas
    if "persona_id" in request.form:
        consulta = consulta.join(Persona)
        consulta = consulta.filter(Persona.id == request.form["persona_id"])
    # Ordenar y paginar
    registros = consulta.order_by(HistorialPuesto.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        periodo = resultado.fecha_inicio.strftime("%Y-%m-%d") + " — ACTUALMENTE"
        if resultado.fecha_termino != None:
            periodo = resultado.fecha_inicio.strftime("%Y-%m-%d") + " — " + resultado.fecha_termino.strftime("%Y-%m-%d")
        data.append(
            {
                "detalle": {
                    "periodo": periodo,
                    "url": url_for("historial_puestos.detail", historial_puesto_id=resultado.id),
                },
                "clave_puesto": resultado.puesto_funcion.puesto.clave,
                "puesto_funcion": resultado.puesto_funcion.nombre,
                "centro_trabajo": resultado.centro_trabajo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@historial_puestos.route("/historial_puestos/<int:historial_puesto_id>")
def detail(historial_puesto_id):
    """Detalle de un Historial de Puesto"""
    historial_puesto = HistorialPuesto.query.get_or_404(historial_puesto_id)
    return render_template("historial_puestos/detail.jinja2", historial_puesto=historial_puesto)


@historial_puestos.route("/historial_puestos/nuevo/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_person(persona_id):
    """Nuevo Historial de Puesto"""
    persona = Persona.query.get_or_404(persona_id)
    form = HistorialPuestoForm()
    if form.validate_on_submit():
        historial_puesto = HistorialPuesto(
            persona=persona,
            nombre=safe_string(form.nombre.data),
        )
        historial_puesto.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Historial de Puesto {historial_puesto.nombre}"),
            url=url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.persona.data = persona.nombre_completo
    return render_template("historial_puestos/new_with_person.jinja2", form=form, persona=persona)
