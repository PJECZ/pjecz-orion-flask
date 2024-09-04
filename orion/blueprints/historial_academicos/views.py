"""
Historial Académico, vistas
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
from orion.blueprints.historial_academicos.models import HistorialAcademico
from orion.blueprints.historial_academicos.forms import HistorialAcademicoForm, HistorialAcademicoWithPersonaForm
from orion.blueprints.personas.models import Persona

MODULO = "HISTORIAL ACADEMICOS"

historial_academicos = Blueprint("historial_academicos", __name__, template_folder="templates")


@historial_academicos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@historial_academicos.route("/historial_academicos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Historial Académicos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = HistorialAcademico.query
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
    registros = consulta.order_by(HistorialAcademico.ano_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "periodo": f"{resultado.ano_inicio} — {resultado.ano_termino}",
                    "url": url_for("historial_academicos.detail", historial_academico_id=resultado.id),
                },
                "nivel": resultado.nivel_academico.nombre,
                "escuela": resultado.nombre_escuela,
                "ciudad": resultado.nombre_ciudad,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@historial_academicos.route("/historial_academicos")
def list_active():
    """Listado de Historial Académicos activos"""
    return render_template(
        "historial_academicos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Historial Académicos",
        estatus="A",
    )


@historial_academicos.route("/historial_academicos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Historial Académicos inactivos"""
    return render_template(
        "historial_academicos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Historial Académicos inactivos",
        estatus="B",
    )


@historial_academicos.route("/historial_academicos/<int:historial_academico_id>")
def detail(historial_academico_id):
    """Detalle de un Historial Académico"""
    historial_academico = HistorialAcademico.query.get_or_404(historial_academico_id)
    return render_template("historial_academicos/detail.jinja2", historial_academico=historial_academico)


@historial_academicos.route("/historial_academicos/nuevo_con_persona_id/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nuevo Historial Académico"""
    persona = Persona.query.get_or_404(persona_id)
    form = HistorialAcademicoWithPersonaForm()
    if form.validate_on_submit():
        if form.ano_inicio.data > form.ano_termino.data:
            flash("El año de inicio no puede ser mayor al año de término.", "warning")
            return render_template("historial_academicos/new_with_persona_id.jinja2", form=form, persona=persona)
        # Guarar registro
        historial_academico = HistorialAcademico(
            persona=persona,
            nivel_academico_id=form.nivel_academico.data,
            nombre_escuela=safe_string(form.nombre_escuela.data, save_enie=True),
            nombre_ciudad=safe_string(form.nombre_ciudad.data, save_enie=True),
            ano_inicio=form.ano_inicio.data,
            ano_termino=form.ano_termino.data,
        )
        historial_academico.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Historial Académico {historial_academico.persona.nombre_completo}"),
            url=url_for("historial_academicos.detail", historial_academico_id=historial_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.persona.data = persona.nombre_completo
    return render_template("historial_academicos/new_with_persona_id.jinja2", form=form, persona=persona)


@historial_academicos.route("/historial_academicos/edicion/<int:historial_academico_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(historial_academico_id):
    """Editar Historial Académicos"""
    historial_academico = HistorialAcademico.query.get_or_404(historial_academico_id)
    form = HistorialAcademicoWithPersonaForm()
    if form.validate_on_submit():
        if form.ano_inicio.data > form.ano_termino.data:
            flash("El año de inicio no puede ser mayor al año de término", "warning")
            return render_template("historial_academicos/edit.jinja2", form=form, historial_academico=historial_academico)
        # Guardar Cambios
        historial_academico.nivel_academico_id = form.nivel_academico.data
        historial_academico.nombre_escuela = safe_string(form.nombre_escuela.data, save_enie=True)
        historial_academico.nombre_ciudad = safe_string(form.nombre_ciudad.data, save_enie=True)
        historial_academico.ano_inicio = form.ano_inicio.data
        historial_academico.ano_termino = form.ano_termino.data
        historial_academico.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Historial Académicos {historial_academico.persona.nombre_completo}"),
            url=url_for("historial_academicos.detail", historial_academico_id=historial_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    # Cargar valores guardados
    form.persona.data = historial_academico.persona.nombre_completo
    form.nivel_academico.data = historial_academico.nivel_academico_id
    form.nombre_escuela.data = historial_academico.nombre_escuela
    form.nombre_ciudad.data = historial_academico.nombre_ciudad
    form.ano_inicio.data = historial_academico.ano_inicio
    form.ano_termino.data = historial_academico.ano_termino
    return render_template("historial_academicos/edit.jinja2", form=form, historial_academico=historial_academico)


@historial_academicos.route("/historial_academicos/eliminar/<int:historial_academico_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(historial_academico_id):
    """Eliminar Historial Académico"""
    historial_academico = HistorialAcademico.query.get_or_404(historial_academico_id)
    if historial_academico.estatus == "A":
        historial_academico.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Historial Académico {historial_academico.id}"),
            url=url_for("historial_academicos.detail", historial_academico_id=historial_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("historial_academicos.detail", historial_academico_id=historial_academico.id))


@historial_academicos.route("/historial_academicos/recuperar/<int:historial_academico_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(historial_academico_id):
    """Recuperar Historial Académico"""
    historial_academico = HistorialAcademico.query.get_or_404(historial_academico_id)
    if historial_academico.estatus == "B":
        historial_academico.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Historial Académico {historial_academico.id}"),
            url=url_for("historial_academicos.detail", historial_academico_id=historial_academico.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("historial_academicos.detail", historial_academico_id=historial_academico.id))
