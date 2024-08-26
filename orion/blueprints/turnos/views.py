"""
Turnos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.turnos.forms import TurnoForm
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.turnos.models import Turno

MODULO = "TURNOS"

turnos = Blueprint("turnos", __name__, template_folder="templates")


@turnos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@turnos.route("/turnos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Turnos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Turno.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Turno.nombre.contains(nombre))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"])
        if descripcion != "":
            consulta = consulta.filter(Turno.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(Turno.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("turnos.detail", turno_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@turnos.route("/turnos")
def list_active():
    """Listado de Turnos activos"""
    return render_template(
        "turnos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Turnos",
        estatus="A",
    )


@turnos.route("/turnos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Turnos inactivos"""
    return render_template(
        "turnos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Turnos inactivos",
        estatus="B",
    )


@turnos.route("/turnos/<int:turno_id>")
def detail(turno_id):
    """Detalle de un Turno"""
    turno = Turno.query.get_or_404(turno_id)
    return render_template("turnos/detail.jinja2", turno=turno)


@turnos.route("/turnos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Turno"""
    form = TurnoForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data, save_enie=True)
        if Turno.query.filter_by(nombre=nombre).first():
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
            return render_template("turnos/new.jinja2", form=form)
        # Guardar
        turno = Turno(
            nombre=nombre,
            descripcion=safe_string(form.descripcion.data),
        )
        turno.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Turno {turno.nombre}"),
            url=url_for("turnos.detail", turno_id=turno.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("turnos/new.jinja2", form=form)


@turnos.route("/turnos/edicion/<int:turno_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(turno_id):
    """Editar Turno"""
    turno = Turno.query.get_or_404(turno_id)
    form = TurnoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data, save_enie=True)
        if turno.nombre != nombre:
            turno_existente = Turno.query.filter_by(nombre=nombre).first()
            if turno_existente and turno_existente.id != turno.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
        if es_valido:
            turno.nombre = nombre
            turno.descripcion = safe_string(form.descripcion.data)
            turno.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Turno {turno.nombre}"),
                url=url_for("turnos.detail", turno_id=turno.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = turno.nombre
    form.descripcion.data = turno.descripcion
    return render_template("turnos/edit.jinja2", form=form, turno=turno)


@turnos.route("/turnos/eliminar/<int:turno_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(turno_id):
    """Eliminar Turno"""
    turno = Turno.query.get_or_404(turno_id)
    if turno.estatus == "A":
        turno.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Turno {turno.nombre}"),
            url=url_for("turnos.detail", turno_id=turno.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("turnos.detail", turno_id=turno.id))


@turnos.route("/turnos/recuperar/<int:turno_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(turno_id):
    """Recuperar Turno"""
    turno = Turno.query.get_or_404(turno_id)
    if turno.estatus == "B":
        turno.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Turno {turno.nombre}"),
            url=url_for("turnos.detail", turno_id=turno.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("turnos.detail", turno_id=turno.id))


@turnos.route("/turnos/query_turnos_json", methods=["POST"])
def query_turnos_json():
    """Proporcionar el JSON de Áreas para elegir en un Select2"""
    consulta = Turno.query.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"]).upper()
        if nombre != "":
            consulta = consulta.filter(Turno.nombre.contains(nombre))
    results = []
    for turno in consulta.order_by(Turno.nombre).limit(15).all():
        results.append(
            {
                "id": turno.id,
                "text": turno.nombre,
            }
        )
    return {"results": results, "pagination": {"more": False}}
