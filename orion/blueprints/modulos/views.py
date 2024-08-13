"""
Modulos, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.forms import ModuloForm
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "MODULOS"

modulos = Blueprint("modulos", __name__, template_folder="templates")


@modulos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@modulos.route("/modulos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Modulos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Modulo.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Modulo.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Modulo.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("modulos.detail", modulo_id=resultado.id),
                },
                "icono": resultado.icono,
                "en_navegacion": resultado.en_navegacion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@modulos.route("/modulos")
def list_active():
    """Listado de Modulos activos"""
    return render_template(
        "modulos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Módulos",
        estatus="A",
    )


@modulos.route("/modulos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Modulos inactivos"""
    return render_template(
        "modulos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Módulos inactivos",
        estatus="B",
    )


@modulos.route("/modulos/<int:modulo_id>")
def detail(modulo_id):
    """Detalle de un Modulo"""
    modulo = Modulo.query.get_or_404(modulo_id)
    return render_template("modulos/detail.jinja2", modulo=modulo)


@modulos.route("/modulos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Modulo"""
    form = ModuloForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data, save_enie=True)
        if Modulo.query.filter_by(nombre=nombre).first():
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
            return render_template("modulos/new.jinja2", form=form)
        # Guardar
        modulo = Modulo(
            nombre=nombre,
            nombre_corto=safe_string(form.nombre_corto.data, do_unidecode=False, to_uppercase=False, save_enie=True),
            icono=form.icono.data,
            ruta=form.ruta.data,
            en_navegacion=form.en_navegacion.data,
            en_plataforma_orion=form.en_plataforma_orion.data,
        )
        modulo.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Modulo {modulo.nombre}"),
            url=url_for("modulos.detail", modulo_id=modulo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("modulos/new.jinja2", form=form)


@modulos.route("/modulos/edicion/<int:modulo_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(modulo_id):
    """Editar Modulo"""
    modulo = Modulo.query.get_or_404(modulo_id)
    form = ModuloForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data, save_enie=True)
        if modulo.nombre != nombre:
            modulo_existente = Modulo.query.filter_by(nombre=nombre).first()
            if modulo_existente and modulo_existente.id != modulo.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
        if es_valido:
            modulo.nombre = nombre
            modulo.nombre_corto = safe_string(form.nombre_corto.data, do_unidecode=False, to_uppercase=False, save_enie=True)
            modulo.icono = form.icono.data
            modulo.ruta = form.ruta.data
            modulo.en_navegacion = form.en_navegacion.data
            modulo.en_plataforma_orion = form.en_plataforma_orion.data
            modulo.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Modulo {modulo.nombre}"),
                url=url_for("modulos.detail", modulo_id=modulo.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = modulo.nombre
    form.nombre_corto.data = modulo.nombre_corto
    form.icono.data = modulo.icono
    form.ruta.data = modulo.ruta
    form.en_navegacion.data = modulo.en_navegacion
    form.en_plataforma_orion.data = modulo.en_plataforma_orion
    return render_template("modulos/edit.jinja2", form=form, modulo=modulo)


@modulos.route("/modulos/eliminar/<int:modulo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(modulo_id):
    """Eliminar Modulo"""
    este_modulo = Modulo.query.get_or_404(modulo_id)
    if este_modulo.estatus == "A":
        # Dar de baja el modulo
        este_modulo.delete()
        # Dar de baja los permisos asociados
        for permiso in este_modulo.permisos:
            permiso.delete()
        # Guardar en la bitacora
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Modulo {este_modulo.nombre}"),
            url=url_for("modulos.detail", modulo_id=este_modulo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("modulos.detail", modulo_id=este_modulo.id))


@modulos.route("/modulos/recuperar/<int:modulo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(modulo_id):
    """Recuperar Modulo"""
    este_modulo = Modulo.query.get_or_404(modulo_id)
    if este_modulo.estatus == "B":
        # Dar de alta el modulo
        este_modulo.recover()
        # Dar de alta los permisos asociados
        for permiso in este_modulo.permisos:
            permiso.recover()
        # Guardar en la bitacora
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Modulo {este_modulo.nombre}"),
            url=url_for("modulos.detail", modulo_id=este_modulo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("modulos.detail", modulo_id=este_modulo.id))
