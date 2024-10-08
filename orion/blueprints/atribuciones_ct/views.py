"""
Atribuciones CT, vistas
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
from orion.blueprints.atribuciones_ct.models import AtribucionCT
from orion.blueprints.areas.models import Area
from orion.blueprints.centros_trabajos.models import CentroTrabajo
from orion.blueprints.atribuciones_ct.forms import AtribucionCTForm

MODULO = "ATRIBUCIONES CT"

atribuciones_ct = Blueprint("atribuciones_ct", __name__, template_folder="templates")


@atribuciones_ct.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@atribuciones_ct.route("/atribuciones_ct/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Atribuciones CT"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = AtribucionCT.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(AtribucionCT.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(AtribucionCT.estatus == "A")
    if "atribucion_ct_id" in request.form:
        consulta = consulta.filter(AtribucionCT.id == request.form["atribucion_ct_id"])
    # Luego filtrar por columnas de otras tablas
    if "area" in request.form:
        nombre = safe_string(request.form["area"], save_enie=True)
        if nombre != "":
            consulta = consulta.join(Area)
            consulta = consulta.filter(Area.nombre.contains(nombre))
    if "centro_trabajo" in request.form:
        clave = safe_string(request.form["centro_trabajo"], save_enie=True)
        if clave != "":
            if "area" not in request.form:
                consulta = consulta.join(Area)
            consulta = consulta.join(CentroTrabajo, Area.centro_trabajo_id == CentroTrabajo.id)
            consulta = consulta.filter(CentroTrabajo.clave.contains(clave))
    # Ordenar y paginar
    registros = consulta.order_by(AtribucionCT.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("atribuciones_ct.detail", atribucion_ct_id=resultado.id),
                },
                "centro_trabajo": {
                    "clave": resultado.area.centro_trabajo.clave,
                    "nombre": resultado.area.centro_trabajo.nombre,
                    "url": url_for("centros_trabajos.detail", centro_trabajo_id=resultado.area.centro_trabajo.id),
                },
                "area": {
                    "nombre": resultado.area.nombre,
                    "url": url_for("areas.detail", area_id=resultado.area.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@atribuciones_ct.route("/atribuciones_ct")
def list_active():
    """Listado de Atribuciones CT activos"""
    return render_template(
        "atribuciones_ct/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Atribuciones CT",
        estatus="A",
    )


@atribuciones_ct.route("/atribuciones_ct/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Atribuciones CT inactivos"""
    return render_template(
        "atribuciones_ct/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Atribuciones CT inactivos",
        estatus="B",
    )


@atribuciones_ct.route("/atribuciones_ct/<int:atribucion_ct_id>")
def detail(atribucion_ct_id):
    """Detalle de un Atribución CT"""
    atribucion_ct = AtribucionCT.query.get_or_404(atribucion_ct_id)
    return render_template("atribuciones_ct/detail.jinja2", atribucion_ct=atribucion_ct)


@atribuciones_ct.route("/atribuciones_ct/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Atribución CT"""
    form = AtribucionCTForm()
    if form.validate_on_submit():
        # Revisar si ya existe la relación de CT y área asignada.
        if AtribucionCT.query.filter(AtribucionCT.area_id == form.area.data).first() is not None:
            flash("Esta Área ya se encuentra asignada.", "warning")
            return render_template("atribuciones_ct/new.jinja2", form=form)
        # Guardar Registro
        atribucion = AtribucionCT(
            area_id=form.area.data,
            norma=safe_string(form.norma.data, save_enie=True),
            fundamento=safe_string(form.fundamento.data, save_enie=True),
            fragmento=safe_string(form.fragmento.data, save_enie=True),
        )
        atribucion.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Atribución CT {atribucion.id}"),
            url=url_for("atribuciones_ct.detail", atribucion_id=atribucion.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("atribuciones_ct/new.jinja2", form=form)


@atribuciones_ct.route("/atribuciones_ct/edicion/<int:atribucion_ct_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(atribucion_ct_id):
    """Editar Atribución CT"""
    atribucion_ct = AtribucionCT.query.get_or_404(atribucion_ct_id)
    form = AtribucionCTForm()
    if form.validate_on_submit():
        # Revisar si ya existe la relación de CT y área asiganda.
        if (
            AtribucionCT.query.filter(AtribucionCT.area_id == form.area.data)
            .filter(AtribucionCT.id != atribucion_ct_id)
            .first()
            is not None
        ):
            flash("Esta Área ya se encuentra asiganada.", "warning")
            return render_template("atribuciones_ct/edit.jinja2", form=form, atribucion_ct=atribucion_ct)
        # Guardar cambios
        atribucion_ct.area_id = form.area.data
        atribucion_ct.norma = safe_string(form.norma.data, save_enie=True)
        atribucion_ct.fundamento = safe_string(form.fundamento.data, save_enie=True)
        atribucion_ct.fragmento = safe_string(form.fragmento.data, save_enie=True)
        atribucion_ct.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Atribución CT {atribucion_ct.norma}"),
            url=url_for("atribuciones_ct.detail", atribucion_ct_id=atribucion_ct.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.norma.data = atribucion_ct.norma
    form.fundamento.data = atribucion_ct.fundamento
    form.fragmento.data = atribucion_ct.fragmento
    return render_template("atribuciones_ct/edit.jinja2", form=form, atribucion_ct=atribucion_ct)


@atribuciones_ct.route("/atribuciones_ct/eliminar/<int:atribucion_ct_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(atribucion_ct_id):
    """Eliminar Atribución CT"""
    atribucion_ct = AtribucionCT.query.get_or_404(atribucion_ct_id)
    if atribucion_ct.estatus == "A":
        atribucion_ct.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Atribución CT {atribucion_ct.id}"),
            url=url_for("atribuciones_ct.detail", atribucion_ct_id=atribucion_ct.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("atribuciones_ct.detail", atribucion_ct_id=atribucion_ct.id))


@atribuciones_ct.route("/atribuciones_ct/recuperar/<int:atribucion_ct_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(atribucion_ct_id):
    """Recuperar Atribución CT"""
    atribucion_ct = AtribucionCT.query.get_or_404(atribucion_ct_id)
    if atribucion_ct.estatus == "B":
        atribucion_ct.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Atribución CT {atribucion_ct.id}"),
            url=url_for("atribuciones_ct.detail", atribucion_ct_id=atribucion_ct.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("atribuciones_ct.detail", atribucion_ct_id=atribucion_ct.id))
