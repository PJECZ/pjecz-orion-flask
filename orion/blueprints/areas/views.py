"""
Áreas, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.areas.forms import AreaForm
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.areas.models import Area

MODULO = "AREAS"

areas = Blueprint("areas", __name__, template_folder="templates")


@areas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@areas.route("/areas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Áreas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Area.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Area.nombre.contains(nombre))
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(Area.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("areas.detail", area_id=resultado.id),
                },
                "centro_trabajo": {
                    "nombre": "FALTA",
                    "url": "#",
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@areas.route("/areas")
def list_active():
    """Listado de Áreas activas"""
    return render_template(
        "areas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Áreas",
        estatus="A",
    )


@areas.route("/areas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Áreas inactivas"""
    return render_template(
        "areas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Áreas inactivas",
        estatus="B",
    )


@areas.route("/areas/<int:area_id>")
def detail(area_id):
    """Detalle de un Área"""
    area = Area.query.get_or_404(area_id)
    return render_template("areas/detail.jinja2", area=area)


@areas.route("/areas/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Área"""
    form = AreaForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data, save_enie=True)
        if Area.query.filter_by(nombre=nombre).first():
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
            return render_template("carreras/new.jinja2", form=form)
        # Guardar
        area = Area(
            nombre=nombre,
            # centro_trabajo=form.centro_trabajo.data,
        )
        area.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Área {area.nombre}"),
            url=url_for("areas.detail", area_id=area.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("areas/new.jinja2", form=form)


@areas.route("/areas/edicion/<int:area_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(area_id):
    """Editar Área"""
    area = Area.query.get_or_404(area_id)
    form = AreaForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data, save_enie=True)
        if area.nombre != nombre:
            area_existente = Area.query.filter_by(nombre=nombre).first()
            if area_existente and area_existente.id != area.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
        if es_valido:
            area.nombre = nombre
            # area.centro_trabajo = safe_string(form.centro_trabajo.data)
            area.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Área {area.nombre}"),
                url=url_for("areas.detail", area_id=area.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = area.nombre
    # form.centro_trabajo.data = area.centro_trabajo
    return render_template("areas/edit.jinja2", form=form, area=area)


@areas.route("/areas/eliminar/<int:area_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(area_id):
    """Eliminar Área"""
    area = Area.query.get_or_404(area_id)
    if area.estatus == "A":
        area.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Área {area.nombre}"),
            url=url_for("areas.detail", area_id=area.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("areas.detail", area_id=area.id))


@areas.route("/areas/recuperar/<int:area_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(area_id):
    """Recuperar Área"""
    area = Area.query.get_or_404(area_id)
    if area.estatus == "B":
        area.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Área {area.nombre}"),
            url=url_for("areas.detail", area_id=area.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("areas.detail", area_id=area.id))
