"""
Bancos, vistas
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
from orion.blueprints.bancos.models import Banco
from orion.blueprints.bancos.forms import BancoForm

MODULO = "BANCOS"

bancos = Blueprint("bancos", __name__, template_folder="templates")


@bancos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@bancos.route("/bancos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Bancos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Banco.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Banco.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Banco.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("bancos.detail", banco_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@bancos.route("/bancos")
def list_active():
    """Listado de Bancos activos"""
    return render_template(
        "bancos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Bancos",
        estatus="A",
    )


@bancos.route("/bancos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Bancos inactivos"""
    return render_template(
        "bancos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Bancos inactivos",
        estatus="B",
    )


@bancos.route("/bancos/<int:banco_id>")
def detail(banco_id):
    """Detalle de un Banco"""
    banco = Banco.query.get_or_404(banco_id)
    return render_template("bancos/detail.jinja2", banco=banco)


@bancos.route("/bancos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Banco"""
    form = BancoForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data, save_enie=True)
        if Banco.query.filter_by(nombre=nombre).first():
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
            return render_template("bancos/new.jinja2", form=form)
        # Guardar
        banco = Banco(nombre=nombre)
        banco.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Banco {banco.nombre}"),
            url=url_for("bancos.detail", banco_id=banco.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("bancos/new.jinja2", form=form)


@bancos.route("/bancos/edicion/<int:banco_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(banco_id):
    """Editar Banco"""
    banco = Banco.query.get_or_404(banco_id)
    form = BancoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data, save_enie=True)
        if banco.nombre != nombre:
            banco_existente = Banco.query.filter_by(nombre=nombre).first()
            if banco_existente and banco_existente.id != banco.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
        if es_valido:
            banco.nombre = safe_string(form.nombre.data)
            banco.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Banco {banco.nombre}"),
                url=url_for("bancos.detail", banco_id=banco.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = banco.nombre
    return render_template("bancos/edit.jinja2", form=form, banco=banco)


@bancos.route("/bancos/eliminar/<int:banco_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(banco_id):
    """Eliminar Banco"""
    banco = Banco.query.get_or_404(banco_id)
    if banco.estatus == "A":
        banco.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Banco {banco.nombre}"),
            url=url_for("bancos.detail", banco_id=banco.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("bancos.detail", banco_id=banco.id))


@bancos.route("/bancos/recuperar/<int:banco_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(banco_id):
    """Recuperar Banco"""
    banco = Banco.query.get_or_404(banco_id)
    if banco.estatus == "B":
        banco.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Banco {banco.nombre}"),
            url=url_for("bancos.detail", banco_id=banco.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("bancos.detail", banco_id=banco.id))
