"""
Municipios, vistas
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
from orion.blueprints.municipios.models import Municipio

from orion.blueprints.municipios.forms import MunicipioForm

MODULO = "MUNICIPIOS"

municipios = Blueprint("municipios", __name__, template_folder="templates")


@municipios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@municipios.route("/municipios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Municipios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Municipio.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        try:
            clave = str(int(request.form["clave"])).zfill(3)
            if clave != "":
                consulta = consulta.filter(Municipio.clave == clave)
        except ValueError:
            pass
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Municipio.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Municipio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("municipios.detail", municipio_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@municipios.route("/municipios/select_json/<int:estado_id>", methods=["GET", "POST"])
def select_json(estado_id=None):
    """Select JSON para Municipios"""
    # Consultar
    consulta = Municipio.query.filter_by(estatus="A").order_by(Municipio.nombre)
    # Elaborar datos para Select
    data = []
    for resultado in consulta.all():
        data.append(
            {
                "id": resultado.id,
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return json.dumps(data)


@municipios.route("/municipios")
def list_active():
    """Listado de Municipios activos"""
    return render_template(
        "municipios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Municipios",
        estatus="A",
    )


@municipios.route("/municipios/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Municipios inactivos"""
    return render_template(
        "municipios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Municipios inactivos",
        estatus="B",
    )


@municipios.route("/municipios/<int:municipio_id>")
def detail(municipio_id):
    """Detalle de un Municipio"""
    municipio = Municipio.query.get_or_404(municipio_id)
    return render_template("municipios/detail.jinja2", municipio=municipio)


@municipios.route("/municipios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Municipio"""
    form = MunicipioForm()
    if form.validate_on_submit():
        municipio = Municipio(
            clave=safe_string(form.clave.data),
            nombre=safe_string(form.nombre.data, save_enie=True),
        )
        municipio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Municipio {municipio.nombre}"),
            url=url_for("municipios.detail", municipio_id=municipio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("municipios/new.jinja2", form=form)


@municipios.route("/municipios/edicion/<int:municipio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(municipio_id):
    """Editar Municipio"""
    municipio = Municipio.query.get_or_404(municipio_id)
    form = MunicipioForm()
    if form.validate_on_submit():
        municipio.clave = safe_string(form.clave.data)
        municipio.nombre = safe_string(form.nombre.data, save_enie=True)
        municipio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Municipio {municipio.nombre}"),
            url=url_for("municipios.detail", municipio_id=municipio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.clave.data = municipio.clave
    form.nombre.data = municipio.nombre
    return render_template("municipios/edit.jinja2", form=form, municipio=municipio)


@municipios.route("/municipios/eliminar/<int:municipio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(municipio_id):
    """Eliminar Municipio"""
    municipio = Municipio.query.get_or_404(municipio_id)
    if municipio.estatus == "A":
        municipio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Municipio {municipio.nombre}"),
            url=url_for("municipios.detail", municipio_id=municipio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("municipios.detail", municipio_id=municipio.id))


@municipios.route("/municipios/recuperar/<int:municipio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(municipio_id):
    """Recuperar Municipio"""
    municipio = Municipio.query.get_or_404(municipio_id)
    if municipio.estatus == "B":
        municipio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Municipio {municipio.nombre}"),
            url=url_for("municipios.detail", municipio_id=municipio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("municipios.detail", municipio_id=municipio.id))
