"""
Puestos Funciones, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.puestos.models import Puesto
from orion.blueprints.puestos_funciones.forms import PuestoFuncionForm
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.puestos_funciones.models import PuestoFuncion

MODULO = "PUESTOS FUNCIONES"

puestos_funciones = Blueprint("puestos_funciones", __name__, template_folder="templates")


@puestos_funciones.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@puestos_funciones.route("/puestos_funciones/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Puestos Funciones"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PuestoFuncion.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(PuestoFuncion.nombre.contains(nombre))
    if "puesto_id" in request.form:
        consulta = consulta.filter(PuestoFuncion.puesto_id == request.form["puesto_id"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(PuestoFuncion.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("puestos_funciones.detail", puesto_funcion_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@puestos_funciones.route("/puestos_funciones/<int:puesto_funcion_id>")
def detail(puesto_funcion_id):
    """Detalle de un Puesto Funcion"""
    puesto_funcion = PuestoFuncion.query.get_or_404(puesto_funcion_id)
    # personas_activas = db.session.query(Persona).join(HistorialPuesto).filter(HistorialPuesto.puesto_funcion_id == puesto_funcion_id).filter(HistorialPuesto.fecha_termino == None).filter(Persona.estatus == "A").limit(100).all()
    return render_template(
        "puestos_funciones/detail.jinja2",
        puesto_funcion=puesto_funcion,
        filtros_personas=json.dumps({"estatus": "A"}),
    )


@puestos_funciones.route("/puestos_funciones/nuevo_con_puesto/<int:puesto_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_puesto(puesto_id):
    """Nuevo Puesto Función"""
    puesto = Puesto.query.get_or_404(puesto_id)
    form = PuestoFuncionForm()
    if form.validate_on_submit():
        puesto_funcion = PuestoFuncion(
            puesto_id=puesto_id,
            nombre=safe_string(form.nombre.data),
        )
        puesto_funcion.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Puesto Función {puesto_funcion.nombre}"),
            url=url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.puesto.data = puesto.clave_nombre
    return render_template("puestos_funciones/new_with_puesto.jinja2", form=form, puesto=puesto)


@puestos_funciones.route("/puestos_funciones/edicion/<int:puesto_funcion_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(puesto_funcion_id):
    """Editar Puesto Función"""
    puesto_funcion = PuestoFuncion.query.get_or_404(puesto_funcion_id)
    form = PuestoFuncionForm()
    if form.validate_on_submit():
        puesto_funcion.nombre = safe_string(form.nombre.data)
        puesto_funcion.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Puesto Función {puesto_funcion.nombre}"),
            url=url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.puesto.data = puesto_funcion.puesto.clave_nombre
    form.nombre.data = puesto_funcion.nombre
    return render_template("puestos_funciones/edit.jinja2", form=form, puesto_funcion=puesto_funcion)


@puestos_funciones.route("/puestos_funciones/eliminar/<int:puesto_funcion_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(puesto_funcion_id):
    """Eliminar Puesto Función"""
    puesto_funcion = PuestoFuncion.query.get_or_404(puesto_funcion_id)
    if puesto_funcion.estatus == "A":
        puesto_funcion.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Puesto Función {puesto_funcion.nombre}"),
            url=url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id))


@puestos_funciones.route("/puestos_funciones/recuperar/<int:puesto_funcion_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(puesto_funcion_id):
    """Recuperar Puesto Función"""
    puesto_funcion = PuestoFuncion.query.get_or_404(puesto_funcion_id)
    if puesto_funcion.estatus == "B":
        puesto_funcion.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Puesto Función {puesto_funcion.nombre}"),
            url=url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("puestos_funciones.detail", puesto_funcion_id=puesto_funcion.id))
