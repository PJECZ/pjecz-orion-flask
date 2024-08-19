"""
Distritos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.distritos.forms import DistritoForm
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.distritos.models import Distrito

MODULO = "DISTRITOS"

distritos = Blueprint("distritos", __name__, template_folder="templates")


@distritos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@distritos.route("/distritos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Distrito"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Distrito.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_string(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(Distrito.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Distrito.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Distrito.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("distritos.detail", distrito_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@distritos.route("/distritos")
def list_active():
    """Listado de Distritos activos"""
    return render_template(
        "distritos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Distritos",
        estatus="A",
    )


@distritos.route("/distritos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Distritos inactivos"""
    return render_template(
        "distritos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Distritos inactivos",
        estatus="B",
    )


@distritos.route("/distritos/<int:distrito_id>")
def detail(distrito_id):
    """Detalle de un Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    filtros_centros_trabajos = json.dumps({"estatus": "A", "distrito_id": distrito.id})
    filtros_personas = json.dumps({"estatus": "A", "distrito_id": distrito.id})
    return render_template(
        "distritos/detail.jinja2",
        distrito=distrito,
        filtros_centros_trabajos=filtros_centros_trabajos,
        filtros_personas=filtros_personas,
    )


@distritos.route("/distritos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Distrito"""
    form = DistritoForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        clave = safe_string(form.clave.data, save_enie=True)
        if Distrito.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("distritos/new.jinja2", form=form)
        # Guardar
        distrito = Distrito(
            clave=clave,
            nombre=safe_string(form.nombre.data, save_enie=True),
        )
        distrito.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Distrito {distrito.nombre}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("distritos/new.jinja2", form=form)


@distritos.route("/distritos/edicion/<int:distrito_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(distrito_id):
    """Editar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    form = DistritoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        clave = safe_string(form.clave.data)
        if distrito.clave != clave:
            distrito_existente = Distrito.query.filter_by(clave=clave).first()
            if distrito_existente and distrito_existente.id != distrito.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            distrito.clave = clave
            distrito.nombre = safe_string(form.nombre.data, save_enie=True)
            distrito.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Distrito {distrito.clave}"),
                url=url_for("distritos.detail", distrito_id=distrito.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = distrito.clave
    form.nombre.data = distrito.nombre
    return render_template("distritos/edit.jinja2", form=form, distrito=distrito)


@distritos.route("/distritos/eliminar/<int:distrito_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(distrito_id):
    """Eliminar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    if distrito.estatus == "A":
        distrito.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Distrito {distrito.clave}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("distritos.detail", distrito_id=distrito.id))


@distritos.route("/distritos/recuperar/<int:distrito_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(distrito_id):
    """Recuperar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    if distrito.estatus == "B":
        distrito.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Distrito {distrito.clave}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("distritos.detail", distrito_id=distrito.id))
