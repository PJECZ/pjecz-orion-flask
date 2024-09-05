"""
Personas Nombramientos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.personas_nombramientos.models import PersonaNombramiento

MODULO = "PERSONAS NOMBRAMIENTOS"

personas_nombramientos = Blueprint("personas_nombramientos", __name__, template_folder="templates")


@personas_nombramientos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_nombramientos.route("/personas_nombramientos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Nombramientos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PersonaNombramiento.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "persona_id" in request.form:
        consulta = consulta.filter_by(persona_id=request.form["persona_id"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(PersonaNombramiento.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
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
                    "url": url_for("personas_nombramientos.detail", persona_nombramiento_id=resultado.id),
                },
                "cargo": resultado.cargo,
                "centro_trabajo": resultado.centro_trabajo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas_nombramientos.route("/personas_nombramientos/<int:persona_nombramiento_id>")
def detail(persona_nombramiento_id):
    """Detalle de un Nombramiento"""
    persona_nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    return render_template("personas_nombramientos/detail.jinja2", persona_nombramiento=persona_nombramiento)


# TODO: NEW_WITH_PERSONA_ID

# TODO: EDIT


@personas_nombramientos.route("/personas_nombramientos/eliminar/<int:persona_nombramiento_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(persona_nombramiento_id):
    """Eliminar Nombramiento"""
    nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    if nombramiento.estatus == "A":
        nombramiento.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Nombramiento {nombramiento.id}"),
            url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id))


@personas_nombramientos.route("/personas_nombramientos/recuperar/<int:persona_nombramiento_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(persona_nombramiento_id):
    """Recuperar Nombramiento"""
    nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    if nombramiento.estatus == "B":
        nombramiento.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Nombramiento {nombramiento.id}"),
            url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id))
