"""
Niveles Académicos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_clave

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.niveles_academicos.forms import NivelAcademicoForm
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.niveles_academicos.models import NivelAcademico

MODULO = "NIVELES ACADEMICOS"

niveles_academicos = Blueprint("niveles_academicos", __name__, template_folder="templates")


@niveles_academicos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@niveles_academicos.route("/niveles_academicos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Niveles Académicos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = NivelAcademico.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(NivelAcademico.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(NivelAcademico.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(NivelAcademico.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("niveles_academicos.detail", nivel_academico_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@niveles_academicos.route("/niveles_academicos")
def list_active():
    """Listado de Niveles Académicos activos"""
    return render_template(
        "niveles_academicos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Niveles Académicos",
        estatus="A",
    )


@niveles_academicos.route("/niveles_academicos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Niveles Académicos inactivos"""
    return render_template(
        "niveles_academicos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Niveles Académicos inactivos",
        estatus="B",
    )


@niveles_academicos.route("/niveles_academicos/<int:nivel_academico_id>")
def detail(nivel_academico_id):
    """Detalle de un Nivel Académico"""
    nivel_academico = NivelAcademico.query.get_or_404(nivel_academico_id)
    return render_template("niveles_academicos/detail.jinja2", nivel_academico=nivel_academico)


@niveles_academicos.route("/niveles_academicos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Nivel Académico"""
    form = NivelAcademicoForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        clave = safe_clave(form.clave.data)
        if NivelAcademico.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("niveles_academicos/new.jinja2", form=form)
        # Guardar
        nivel_academico = NivelAcademico(
            clave=clave,
            nombre=safe_string(form.nombre.data, save_enie=True),
        )
        nivel_academico.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Nivel Académico {nivel_academico.clave}"),
            url=url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("niveles_academicos/new.jinja2", form=form)


@niveles_academicos.route("/niveles_academicos/edicion/<int:nivel_academico_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(nivel_academico_id):
    """Editar Nivel Académico"""
    nivel_academico = NivelAcademico.query.get_or_404(nivel_academico_id)
    form = NivelAcademicoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if nivel_academico.clave != clave:
            nivel_academico_existente = nivel_academico.query.filter_by(clave=clave).first()
            if nivel_academico_existente and nivel_academico_existente.id != nivel_academico.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            nivel_academico.nombre = safe_string(form.nombre.data)
            nivel_academico.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Nivel Académico {nivel_academico.nombre}"),
                url=url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = nivel_academico.clave
    form.nombre.data = nivel_academico.nombre
    return render_template("niveles_academicos/edit.jinja2", form=form, nivel_academico=nivel_academico)


@niveles_academicos.route("/niveles_academicos/eliminar/<int:nivel_academico_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(nivel_academico_id):
    """Eliminar Nivel Académico"""
    nivel_academico = NivelAcademico.query.get_or_404(nivel_academico_id)
    if nivel_academico.estatus == "A":
        nivel_academico.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Nivel Académico {nivel_academico.nombre}"),
            url=url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id))


@niveles_academicos.route("/niveles_academicos/recuperar/<int:nivel_academico_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(nivel_academico_id):
    """Recuperar Nivel Académico"""
    nivel_academico = NivelAcademico.query.get_or_404(nivel_academico_id)
    if nivel_academico.estatus == "B":
        nivel_academico.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Nivel Académico {nivel_academico.nombre}"),
            url=url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("niveles_academicos.detail", nivel_academico_id=nivel_academico.id))
