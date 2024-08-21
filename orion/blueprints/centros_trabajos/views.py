"""
Centros de Trabajo, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_clave

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.centros_trabajos.forms import CentroTrabajoForm
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.centros_trabajos.models import CentroTrabajo

MODULO = "CENTROS TRABAJOS"

centros_trabajos = Blueprint("centros_trabajos", __name__, template_folder="templates")


@centros_trabajos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@centros_trabajos.route("/centros_trabajos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Centros de Trabajos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CentroTrabajo.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(CentroTrabajo.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(CentroTrabajo.nombre.contains(nombre))
    if "distrito_id" in request.form:
        consulta = consulta.filter_by(distrito_id=request.form["distrito_id"])
    if "organo_id" in request.form:
        consulta = consulta.filter_by(organo_id=request.form["organo_id"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(CentroTrabajo.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("centros_trabajos.detail", centro_trabajo_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@centros_trabajos.route("/centros_trabajos")
def list_active():
    """Listado de Centros de Trabajos activos"""
    return render_template(
        "centros_trabajos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Centros de Trabajos",
        estatus="A",
    )


@centros_trabajos.route("/centros_trabajos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Centros de Trabajos inactivos"""
    return render_template(
        "centros_trabajos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Centros de Trabajos inactivos",
        estatus="B",
    )


@centros_trabajos.route("/centros_trabajos/<int:centro_trabajo_id>")
def detail(centro_trabajo_id):
    """Detalle de un Centro de Trabajo"""
    centro_trabajo = CentroTrabajo.query.get_or_404(centro_trabajo_id)
    return render_template("centros_trabajos/detail.jinja2", centro_trabajo=centro_trabajo)


@centros_trabajos.route("/centros_trabajos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Centro de Trabajo"""
    form = CentroTrabajoForm()
    if form.validate_on_submit():
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if CentroTrabajo.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("centros_trabajos/new.jinja2", form=form)
        # Guardar
        centro_trabajo = CentroTrabajo(
            clave=clave,
            nombre=safe_string(form.nombre.data),
            distrito_id=form.distrito.data,
            organo_id=form.organo.data,
            telefono=safe_string(form.telefono.data),
            num_ext=safe_string(form.num_ext.data),
            activo=form.activo.data,
        )
        centro_trabajo.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Centro de Trabajo {centro_trabajo.clave}"),
            url=url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("centros_trabajos/new.jinja2", form=form)


@centros_trabajos.route("/centros_trabajos/edicion/<int:centro_trabajo_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(centro_trabajo_id):
    """Editar Centro de Trabajo"""
    centro_trabajo = CentroTrabajo.query.get_or_404(centro_trabajo_id)
    form = CentroTrabajoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if centro_trabajo.clave != clave:
            CentroTrabajoForm_existente = CentroTrabajo.query.filter_by(clave=clave).first()
            if CentroTrabajoForm_existente and CentroTrabajoForm_existente.id != centro_trabajo.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            centro_trabajo.clave = clave
            centro_trabajo.nombre = safe_string(form.nombre.data)
            centro_trabajo.distrito_id = form.distrito.data
            centro_trabajo.organo_id = form.organo.data
            centro_trabajo.telefono = safe_string(form.telefono.data)
            centro_trabajo.num_ext = safe_string(form.num_ext.data)
            centro_trabajo.activo = form.activo.data
            centro_trabajo.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Centro de Trabajo {centro_trabajo.clave}"),
                url=url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = centro_trabajo.clave
    form.nombre.data = centro_trabajo.nombre
    form.distrito.data = centro_trabajo.distrito.id
    form.organo.data = centro_trabajo.organo.id
    form.telefono.data = centro_trabajo.telefono
    form.num_ext.data = centro_trabajo.num_ext
    form.activo.data = centro_trabajo.activo
    return render_template("centros_trabajos/edit.jinja2", form=form, centro_trabajo=centro_trabajo)


@centros_trabajos.route("/centros_trabajos/eliminar/<int:centro_trabajo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(centro_trabajo_id):
    """Eliminar Centro de Trabajo"""
    centro_trabajo = CentroTrabajo.query.get_or_404(centro_trabajo_id)
    if centro_trabajo.estatus == "A":
        centro_trabajo.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Centro de Trabajo {centro_trabajo.clave}"),
            url=url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id))


@centros_trabajos.route("/centros_trabajos/recuperar/<int:centro_trabajo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(centro_trabajo_id):
    """Recuperar Centro de Trabajo"""
    centro_trabajo = CentroTrabajo.query.get_or_404(centro_trabajo_id)
    if centro_trabajo.estatus == "B":
        centro_trabajo.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Centro de Trabajo {centro_trabajo.clave}"),
            url=url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("centros_trabajos.detail", centro_trabajo_id=centro_trabajo.id))


@centros_trabajos.route("/centros_trabajos/query_centros_trabajos_json", methods=["POST"])
def query_centros_trabajos_json():
    """Proporcionar el JSON de Centros de Trabajos para elegir en un Select2"""
    consulta = CentroTrabajo.query.filter_by(estatus="A")
    if "clave_nombre" in request.form:
        clave_nombre = safe_string(request.form["clave_nombre"]).upper()
        if clave_nombre != "":
            consulta = consulta.filter(
                or_(CentroTrabajo.clave.contains(clave_nombre), CentroTrabajo.nombre.contains(clave_nombre))
            )
    results = []
    for centro_trabajo in consulta.order_by(CentroTrabajo.id).limit(15).all():
        results.append(
            {
                "id": centro_trabajo.id,
                "text": centro_trabajo.clave_nombre,
            }
        )
    return {"results": results, "pagination": {"more": False}}
