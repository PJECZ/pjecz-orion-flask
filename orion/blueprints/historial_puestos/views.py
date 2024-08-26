"""
Historial Puestos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.areas.models import Area
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.centros_trabajos.models import CentroTrabajo
from orion.blueprints.historial_puestos.forms import HistorialPuestoForm
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.historial_puestos.models import HistorialPuesto

MODULO = "HISTORIAL PUESTOS"

historial_puestos = Blueprint("historial_puestos", __name__, template_folder="templates")


@historial_puestos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@historial_puestos.route("/historial_puestos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Historial de Puestos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = HistorialPuesto.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(HistorialPuesto.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(HistorialPuesto.estatus == "A")
    # if "persona_id" in request.form:
    #     consulta = consulta.filter_by(persona_id=request.form["persona_id"])
    # Luego filtrar por columnas de otras tablas
    if "persona_id" in request.form:
        consulta = consulta.join(Persona)
        consulta = consulta.filter(Persona.id == request.form["persona_id"])
    # Ordenar y paginar
    registros = consulta.order_by(HistorialPuesto.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        periodo = resultado.fecha_inicio.strftime("%Y-%m-%d") + " — ACTUALMENTE"
        if resultado.fecha_termino != None:
            periodo = resultado.fecha_inicio.strftime("%Y-%m-%d") + " — " + resultado.fecha_termino.strftime("%Y-%m-%d")
        data.append(
            {
                "detalle": {
                    "periodo": periodo,
                    "url": url_for("historial_puestos.detail", historial_puesto_id=resultado.id),
                },
                "clave_puesto": resultado.puesto_funcion.puesto.clave,
                "puesto_funcion": resultado.puesto_funcion.nombre,
                "centro_trabajo": resultado.centro_trabajo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@historial_puestos.route("/historial_puestos/<int:historial_puesto_id>")
def detail(historial_puesto_id):
    """Detalle de un Historial de Puesto"""
    historial_puesto = HistorialPuesto.query.get_or_404(historial_puesto_id)
    return render_template("historial_puestos/detail.jinja2", historial_puesto=historial_puesto)


@historial_puestos.route("/historial_puestos/nuevo/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_person(persona_id):
    """Nuevo Historial de Puesto"""
    persona = Persona.query.get_or_404(persona_id)
    form = HistorialPuestoForm()
    if form.validate_on_submit():
        # Validar fechas
        if form.fecha_termino.data != None and form.fecha_inicio.data > form.fecha_termino.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de término.", "warning")
            return render_template("historial_puestos/new_with_person.jinja2", form=form, persona=persona)
        # Validar Centro de Trabajo
        centro_trabajo = CentroTrabajo.query.get(form.centro_trabajo.data)
        if centro_trabajo is None:
            flash("Error: No se localiza el Centro de Trabajo elegida.", "danger")
            return render_template("historial_puestos/new_with_person.jinja2", form=form, persona=persona)
        # Validar Área
        area = Area.query.get(form.area.data)
        if area is None:
            flash("Error: No se localiza el Área elegida.", "danger")
            return render_template("historial_puestos/new_with_person.jinja2", form=form, persona=persona)
        # Guardar registro
        historial_puesto = HistorialPuesto(
            persona=persona,
            puesto_funcion_id=form.funcion.data,
            turno_id=form.turno.data,
            area=area.nombre,
            centro_trabajo=centro_trabajo.clave,
            fecha_inicio=form.fecha_inicio.data,
            fecha_termino=form.fecha_termino.data,
            nivel=form.nivel.data,
            quinquenio=form.quinquenio.data,
            nombramiento=safe_string(form.nombramiento.data, save_enie=True),
            tipo_nombramiento=safe_string(form.tipo_nombramiento.data, save_enie=True),
            nombramiento_observaciones=safe_string(form.nombramiento_observaciones.data, save_enie=True),
        )
        historial_puesto.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Historial de Puesto {historial_puesto.id}"),
            url=url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.persona.data = persona.nombre_completo
    return render_template("historial_puestos/new_with_person.jinja2", form=form, persona=persona)


@historial_puestos.route("/historial_puestos/edicion/<int:historial_puesto_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(historial_puesto_id):
    """Editar Historial de Puesto"""
    historial_puesto = HistorialPuesto.query.get_or_404(historial_puesto_id)
    form = HistorialPuestoForm()
    if form.validate_on_submit():
        # Validar fechas
        if form.fecha_termino.data != None and form.fecha_inicio.data > form.fecha_termino.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de término.", "warning")
            return render_template("historial_puestos/edit.jinja2", form=form, historial_puesto=historial_puesto)
        # Validar Centro de Trabajo
        centro_trabajo = CentroTrabajo.query.get(form.centro_trabajo.data)
        if centro_trabajo is None:
            flash("Error: No se localiza el Centro de Trabajo elegido.", "danger")
            return render_template("historial_puestos/edit.jinja2", form=form, historial_puesto=historial_puesto)
        # Validar Área
        area = Area.query.get(form.area.data)
        if area is None:
            flash("Error: No se localiza el Área elegida.", "danger")
            return render_template("historial_puestos/edit.jinja2", form=form, historial_puesto=historial_puesto)
        # Guardar registro
        historial_puesto.puesto_funcion_id = form.funcion.data
        historial_puesto.centro_trabajo = centro_trabajo.clave
        historial_puesto.area = area.nombre
        historial_puesto.turno_id = form.turno.data
        historial_puesto.fecha_inicio = form.fecha_inicio.data
        historial_puesto.fecha_termino = form.fecha_termino.data
        historial_puesto.nivel = form.nivel.data
        historial_puesto.quinquenio = form.quinquenio.data
        historial_puesto.nombramiento = safe_string(form.nombramiento.data, save_enie=True)
        historial_puesto.tipo_nombramiento = safe_string(form.tipo_nombramiento.data, save_enie=True)
        historial_puesto.nombramiento_observaciones = safe_string(form.nombramiento_observaciones.data, save_enie=True)
        # Guardar cambios
        historial_puesto.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Historial de Puesto {historial_puesto.id}"),
            url=url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    # Cargar valores almacenados
    form.persona.data = historial_puesto.persona.nombre_completo
    form.funcion.data = historial_puesto.puesto_funcion
    form.area.data = historial_puesto.area
    form.centro_trabajo.data = historial_puesto.centro_trabajo
    form.turno.data = historial_puesto.turno
    form.fecha_inicio.data = historial_puesto.fecha_inicio
    form.fecha_termino.data = historial_puesto.fecha_termino
    form.nivel.data = historial_puesto.nivel
    form.quinquenio.data = historial_puesto.quinquenio
    form.nombramiento.data = historial_puesto.nombramiento
    form.tipo_nombramiento.data = historial_puesto.tipo_nombramiento
    form.nombramiento_observaciones.data = historial_puesto.nombramiento_observaciones
    return render_template(
        "historial_puestos/edit.jinja2",
        form=form,
        historial_puesto=historial_puesto,
        centro_trabajo=CentroTrabajo.query.filter(CentroTrabajo.clave == form.centro_trabajo.data).first(),
        area=Area.query.filter(Area.nombre == form.area.data).first(),
    )


@historial_puestos.route("/historial_puestos/eliminar/<int:historial_puesto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(historial_puesto_id):
    """Eliminar Historial de Puesto"""
    historial_puesto = HistorialPuesto.query.get_or_404(historial_puesto_id)
    if historial_puesto.estatus == "A":
        historial_puesto.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Historial de Puesto {historial_puesto.id}"),
            url=url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id))


@historial_puestos.route("/historial_puestos/recuperar/<int:historial_puesto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(historial_puesto_id):
    """Recuperar Historial de Puesto"""
    historial_puesto = HistorialPuesto.query.get_or_404(historial_puesto_id)
    if historial_puesto.estatus == "B":
        historial_puesto.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Historial de Puesto {historial_puesto.id}"),
            url=url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("historial_puestos.detail", historial_puesto_id=historial_puesto.id))
