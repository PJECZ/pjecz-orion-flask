"""
Carreras, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.carreras.forms import CarreraForm
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
    """Listado de Carreras activas"""
    return render_template(
        "carreras/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Carreras",
        estatus="A",
    )


@carreras.route("/carreras/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Carreras inactivas"""
    return render_template(
        "carreras/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Carreras inactivas",
        estatus="B",
    )


@carreras.route("/carreras/<int:carrera_id>")
def detail(carrera_id):
    """Detalle de una Carrera"""
    carrera = Carrera.query.get_or_404(carrera_id)
    return render_template("carreras/detail.jinja2", carrera=carrera)


@carreras.route("/carreras/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Carrera"""
    form = CarreraForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data, save_enie=True)
        if Carrera.query.filter_by(nombre=nombre).first():
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
            return render_template("carreras/new.jinja2", form=form)
        # Guardar
        carrera = Carrera(nombre=nombre)
        carrera.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Carrera {carrera.nombre}"),
            url=url_for("carreras.detail", carrera_id=carrera.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("carreras/new.jinja2", form=form)


@carreras.route("/carreras/edicion/<int:carrera_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(carrera_id):
    """Editar Carrera"""
    carrera = Carrera.query.get_or_404(carrera_id)
    form = CarreraForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data, save_enie=True)
        if carrera.nombre != nombre:
            carrera_existente = Carrera.query.filter_by(nombre=nombre).first()
            if carrera_existente and carrera_existente.id != carrera.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
        if es_valido:
            carrera.nombre = safe_string(form.nombre.data)
            carrera.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Carrera {carrera.nombre}"),
                url=url_for("carreras.detail", carrera_id=carrera.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = carrera.nombre
    return render_template("carreras/edit.jinja2", form=form, carrera=carrera)


@carreras.route("/carreras/eliminar/<int:carrera_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(carrera_id):
    """Eliminar Carrera"""
    carrera = Carrera.query.get_or_404(carrera_id)
    if carrera.estatus == "A":
        carrera.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Carrera {carrera.nombre}"),
            url=url_for("carreras.detail", carrera_id=carrera.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("carreras.detail", carrera_id=carrera.id))


@carreras.route("/carreras/recuperar/<int:carrera_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(carrera_id):
    """Recuperar Carrera"""
    carrera = Carrera.query.get_or_404(carrera_id)
    if carrera.estatus == "B":
        carrera.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Carrera {carrera.nombre}"),
            url=url_for("carreras.detail", carrera_id=carrera.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("carreras.detail", carrera_id=carrera.id))
