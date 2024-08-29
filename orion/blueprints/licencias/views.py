"""
Licencias, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.historial_puestos.models import HistorialPuesto
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.licencias.models import Licencia
from orion.blueprints.licencias.forms import LicenciaForm, LicenciaWithPersonaForm

MODULO = "LICENCIAS"

licencias = Blueprint("licencias", __name__, template_folder="templates")


@licencias.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@licencias.route("/licencias/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Licencias"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Licencia.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "fecha_inicio" in request.form:
        consulta = consulta.filter(Licencia.fecha_inicio >= request.form["fecha_inicio"])
    if "fecha_termino" in request.form:
        consulta = consulta.filter(Licencia.fecha_termino <= request.form["fecha_termino"])
    if "tipo" in request.form:
        consulta = consulta.filter(Licencia.tipo == request.form["tipo"])
    # Luego filtrar por columnas de otras tablas
    if "persona_nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["persona_nombre_completo"])
        if nombre_completo != "":
            consulta = consulta.join(Persona)
            for palabra in nombre_completo.split(" "):
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    # Ordenar y paginar
    registros = consulta.order_by(Licencia.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "periodo": resultado.fecha_inicio.strftime("%Y-%m-%d")
                    + " — "
                    + resultado.fecha_termino.strftime("%Y-%m-%d"),
                    "url": url_for("licencias.detail", licencia_id=resultado.id),
                },
                "tipo": resultado.tipo,
                "dias": f"{(resultado.fecha_termino - resultado.fecha_inicio).days + 1} DÍAS",
                "persona": {
                    "nombre": resultado.persona.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.persona.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@licencias.route("/licencias")
def list_active():
    """Listado de Licencias activos"""
    return render_template(
        "licencias/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Licencias",
        tipos=Licencia.TIPOS,
        estatus="A",
    )


@licencias.route("/licencias/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Licencias inactivas"""
    return render_template(
        "licencias/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Licencias inactivas",
        tipos=Licencia.TIPOS,
        estatus="B",
    )


@licencias.route("/licencias/<int:licencia_id>")
def detail(licencia_id):
    """Detalle de una Licencia"""
    licencia = Licencia.query.get_or_404(licencia_id)
    return render_template("licencias/detail.jinja2", licencia=licencia)


@licencias.route("/licencias/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Licencia"""
    form = LicenciaForm()
    if form.validate_on_submit():
        if form.fecha_termino.data < form.fecha_inicio.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de termino.", "warning")
            return render_template("licencias/new.jinja2", form=form)
        # Leer el historial de puestos para extraer el nombre del puesto en esa fecha.
        historial_puesto = HistorialPuesto.query.filter_by(persona=form.persona.data).filter_by(estatus="A")
        historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
        historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
        puesto_nombre = None
        if historial_puesto:
            puesto_nombre = historial_puesto.puesto_funcion.nombre
        # Guardar la Licencia
        liciencia = Licencia(
            persona_id=form.persona.data,
            tipo=form.tipo.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_termino=form.fecha_termino.data,
            con_goce=form.con_goce.data,
            motivo=safe_string(form.motivo.data, save_enie=True),
            puesto_nombre=puesto_nombre,
        )
        liciencia.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Licencia {liciencia.persona.nombre_completo}"),
            url=url_for("licencias.detail", liciencia_id=liciencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("licencias/new.jinja2", form=form)


@licencias.route("/licencias/nuevo_con_persona/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nueva Licencia con Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = LicenciaWithPersonaForm()
    if form.validate_on_submit():
        if form.fecha_termino.data < form.fecha_inicio.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de termino.", "warning")
            return render_template("licencias/new_with_persona_id.jinja2", form=form, persona=persona)
        # Leer el historial de puestos para extraer el nombre del puesto en esa fecha.
        historial_puesto = HistorialPuesto.query.filter_by(persona=persona).filter_by(estatus="A")
        historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
        historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
        puesto_nombre = None
        if historial_puesto:
            puesto_nombre = historial_puesto.puesto_funcion.nombre
        # Guardar la Licencia
        liciencia = Licencia(
            persona=persona,
            tipo=form.tipo.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_termino=form.fecha_termino.data,
            con_goce=form.con_goce.data,
            motivo=safe_string(form.motivo.data, save_enie=True),
            puesto_nombre=puesto_nombre,
        )
        liciencia.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nueva Licencia {liciencia.persona.nombre_completo}"),
            url=url_for("licencias.detail", liciencia_id=liciencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.persona.data = persona.nombre_completo
    return render_template("licencias/new_with_persona_id.jinja2", form=form, persona=persona)


@licencias.route("/licencias/edicion/<int:licencia_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(licencia_id):
    """Editar Licencia"""
    licencia = Licencia.query.get_or_404(licencia_id)
    form = LicenciaWithPersonaForm()
    if form.validate_on_submit():
        if form.fecha_inicio.data > form.fecha_termino.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de término", "warning")
            return render_template("licencias/edit.jinja2", form=form, licencia=licencia)
        # Guardar el historial de puesto.
        historial_puesto = HistorialPuesto.query.filter_by(persona=licencia.persona).filter_by(estatus="A")
        historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
        historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
        licencia.puesto_nombre = None
        if historial_puesto:
            licencia.puesto_nombre = historial_puesto.puesto_funcion.nombre
        licencia.tipo = form.tipo.data
        licencia.fecha_inicio = form.fecha_inicio.data
        licencia.fecha_termino = form.fecha_termino.data
        licencia.con_goce = form.con_goce.data
        licencia.motivo = safe_string(form.motivo.data, save_enie=True)
        licencia.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Licencia {licencia.persona}"),
            url=url_for("licencias.detail", licencia_id=licencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.persona.data = licencia.persona.nombre_completo
    form.tipo.data = licencia.tipo
    form.fecha_inicio.data = licencia.fecha_inicio
    form.fecha_termino.data = licencia.fecha_termino
    form.con_goce.data = licencia.con_goce
    form.motivo.data = licencia.motivo
    return render_template("licencias/edit.jinja2", form=form, licencia=licencia)


@licencias.route("/licencias/eliminar/<int:licencia_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(licencia_id):
    """Eliminar Licencia"""
    licencia = Licencia.query.get_or_404(licencia_id)
    if licencia.estatus == "A":
        licencia.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Licencia {licencia.persona.nombre_completo}"),
            url=url_for("licencias.detail", licencia_id=licencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("licencias.detail", licencia_id=licencia.id))


@licencias.route("/licencias/recuperar/<int:licencia_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(licencia_id):
    """Recuperar Licencia"""
    licencia = Licencia.query.get_or_404(licencia_id)
    if licencia.estatus == "B":
        licencia.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Licencia {licencia.persona.nombre_completo}"),
            url=url_for("licencias.detail", licencia_id=licencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("licencias.detail", licencia_id=licencia.id))
