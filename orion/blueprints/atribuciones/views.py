"""
Atribuciones, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_clave

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.atribuciones.models import Atribucion
from orion.blueprints.atribuciones.forms import AtribucionForm
from orion.blueprints.puestos_funciones.models import PuestoFuncion
from orion.blueprints.puestos.models import Puesto
from orion.blueprints.centros_trabajos.models import CentroTrabajo

MODULO = "ATRIBUCIONES"

atribuciones = Blueprint("atribuciones", __name__, template_folder="templates")


@atribuciones.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@atribuciones.route("/atribuciones/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Atribuciones"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Atribucion.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(Atribucion.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(Atribucion.estatus == "A")
    if "atribucion_id" in request.form:
        consulta = consulta.filter(Atribucion.id == request.form["atribucion_id"])
    if "tipo" in request.form:
        consulta = consulta.filter(Atribucion.tipo_cargo == request.form["tipo"])
    # Luego filtrar por columnas de otras tablas
    if "funcion" in request.form:
        funcion = safe_string(request.form["funcion"], save_enie=True)
        if funcion != "":
            consulta = consulta.join(PuestoFuncion)
            consulta = consulta.filter(PuestoFuncion.nombre.contains(funcion))
    if "centro_trabajo" in request.form:
        centro_trabajo = safe_clave(request.form["centro_trabajo"])
        if centro_trabajo != "":
            consulta = consulta.join(CentroTrabajo)
            consulta = consulta.filter(CentroTrabajo.clave.contains(centro_trabajo))
    # if "puesto" in request.form:
    # TODO: Hacer join con Puesto a PuestoFuncion con Atribuciones
    #     puesto = safe_clave(request.form["puesto"])
    #     if puesto != "":
    #         consulta = consulta.join(Puesto)
    # Ordenar y paginar
    registros = consulta.order_by(Atribucion.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("atribuciones.detail", atribucion_id=resultado.id),
                },
                "funcion": {
                    "nombre": resultado.funcion.nombre,
                    "url": url_for("puestos_funciones.detail", puesto_funcion_id=resultado.funcion.id),
                },
                "tipo_cargo": Atribucion.CARGOS[resultado.tipo_cargo],
                "puesto": {
                    "texto": resultado.funcion.puesto.clave,
                    "descripcion": resultado.funcion.puesto.nombre,
                    "url": url_for("puestos.detail", puesto_id=resultado.funcion.puesto.id),
                },
                "centro_trabajo": {
                    "texto": resultado.centro_trabajo.clave,
                    "descripcion": resultado.centro_trabajo.nombre,
                    "url": url_for("centros_trabajos.detail", centro_trabajo_id=resultado.centro_trabajo.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@atribuciones.route("/atribuciones")
def list_active():
    """Listado de Atribuciones activos"""
    return render_template(
        "atribuciones/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Atribuciones",
        tipos_cargos=Atribucion.CARGOS,
        estatus="A",
    )


@atribuciones.route("/atribuciones/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Atribuciones inactivos"""
    return render_template(
        "atribuciones/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Atribuciones inactivos",
        tipos_cargos=Atribucion.CARGOS,
        estatus="B",
    )


@atribuciones.route("/atribuciones/<int:atribucion_id>")
def detail(atribucion_id):
    """Detalle de un Atribución"""
    atribucion = Atribucion.query.get_or_404(atribucion_id)
    return render_template("atribuciones/detail.jinja2", atribucion=atribucion)


@atribuciones.route("/atribuciones/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Atribución"""
    form = AtribucionForm()
    if form.validate_on_submit():
        atribucion = Atribucion(
            centro_trabajo_id=form.centro_trabajo.data,
            funcion_id=form.funcion.data,
            tipo_cargo=form.tipo_cargo.data,
            norma=safe_string(form.norma.data, save_enie=True),
            fundamento=safe_string(form.fundamento.data, save_enie=True),
            fragmento=safe_string(form.fragmento.data, save_enie=True),
        )
        atribucion.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Atribución {atribucion.id}"),
            url=url_for("atribuciones.detail", atribucion_id=atribucion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("atribuciones/new.jinja2", form=form)


@atribuciones.route("/atribuciones/edicion/<int:atribucion_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(atribucion_id):
    """Editar Atribución"""
    atribucion = Atribucion.query.get_or_404(atribucion_id)
    form = AtribucionForm()
    if form.validate_on_submit():
        atribucion.centro_trabajo_id = form.centro_trabajo.data
        atribucion.funcion_id = form.funcion.data
        atribucion.tipo_cargo = form.tipo_cargo.data
        atribucion.norma = safe_string(form.norma.data, save_enie=True)
        atribucion.fundamento = safe_string(form.fundamento.data, save_enie=True)
        atribucion.fragmento = safe_string(form.fragmento.data, save_enie=True)
        atribucion.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Atribución {atribucion.norma}"),
            url=url_for("atribuciones.detail", atribucion_id=atribucion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.tipo_cargo.data = atribucion.tipo_cargo
    form.norma.data = atribucion.norma
    form.fundamento.data = atribucion.fundamento
    form.fragmento.data = atribucion.fragmento
    return render_template("atribuciones/edit.jinja2", form=form, atribucion=atribucion)


@atribuciones.route("/atribuciones/eliminar/<int:atribucion_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(atribucion_id):
    """Eliminar Atribución"""
    atribucion = Atribucion.query.get_or_404(atribucion_id)
    if atribucion.estatus == "A":
        atribucion.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Atribución {atribucion.id}"),
            url=url_for("atribuciones.detail", atribucion_id=atribucion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("atribuciones.detail", atribucion_id=atribucion.id))


@atribuciones.route("/atribuciones/recuperar/<int:atribucion_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(atribucion_id):
    """Recuperar Atribución"""
    atribucion = Atribucion.query.get_or_404(atribucion_id)
    if atribucion.estatus == "B":
        atribucion.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Atribución {atribucion.id}"),
            url=url_for("atribuciones.detail", atribucion_id=atribucion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("atribuciones.detail", atribucion_id=atribucion.id))
