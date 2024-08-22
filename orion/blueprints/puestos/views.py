"""
Puestos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_clave

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.puestos.forms import PuestoForm
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.puestos.models import Puesto

MODULO = "PUESTOS"

puestos = Blueprint("puestos", __name__, template_folder="templates")


@puestos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@puestos.route("/puestos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Puestos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Puesto.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(Puesto.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Puesto.nombre.contains(nombre))
    if "tipo_cargo" in request.form:
        consulta = consulta.filter_by(tipo_cargo=request.form["tipo_cargo"])
    if "tipo_empleado" in request.form:
        consulta = consulta.filter_by(tipo_empleado=request.form["tipo_empleado"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(Puesto.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("puestos.detail", puesto_id=resultado.id),
                },
                "nombre": resultado.nombre,
                "tipo_cargo": Puesto.CARGOS[resultado.tipo_cargo],
                "tipo_empleado": {
                    "nombre": resultado.tipo_empleado,
                    "descripcion": Puesto.TIPOS_EMPLEADOS[resultado.tipo_empleado],
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@puestos.route("/puestos")
def list_active():
    """Listado de Puestos activos"""
    return render_template(
        "puestos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Puestos",
        tipos_cargos=Puesto.CARGOS,
        tipos_empleados=Puesto.TIPOS_EMPLEADOS,
        estatus="A",
    )


@puestos.route("/puestos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Puestos inactivos"""
    return render_template(
        "puestos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Puestos inactivos",
        tipos_cargos=Puesto.CARGOS,
        tipos_empleados=Puesto.TIPOS_EMPLEADOS,
        estatus="B",
    )


@puestos.route("/puestos/<int:puesto_id>")
def detail(puesto_id):
    """Detalle de un Puesto"""
    puesto = Puesto.query.get_or_404(puesto_id)
    return render_template(
        "puestos/detail.jinja2",
        puesto=puesto,
        filtros_puestos_funciones=json.dumps({"estatus": "A", "puesto_id": puesto.id}),
    )


@puestos.route("/puestos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Puesto"""
    form = PuestoForm()
    if form.validate_on_submit():
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if Puesto.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("puestos/new.jinja2", form=form)
        # Guardar
        puesto = Puesto(
            clave=clave,
            nombre=safe_string(form.nombre.data),
            tipo_cargo=form.tipo_cargo.data,
            tipo_empleado=form.tipo_empleado.data,
        )
        puesto.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Puesto {puesto.clave}"),
            url=url_for("puestos.detail", puesto_id=puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("puestos/new.jinja2", form=form)


@puestos.route("/puestos/edicion/<int:puesto_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(puesto_id):
    """Editar Puesto"""
    puesto = Puesto.query.get_or_404(puesto_id)
    form = PuestoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if puesto.clave != clave:
            puesto_existente = Puesto.query.filter_by(clave=clave).first()
            if puesto_existente and puesto_existente.id != puesto.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            puesto.clave = clave
            puesto.nombre = safe_string(form.nombre.data)
            puesto.tipo_cargo = form.tipo_cargo.data
            puesto.tipo_empleado = form.tipo_empleado.data
            puesto.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Puesto {puesto.clave}"),
                url=url_for("puestos.detail", puesto_id=puesto.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = puesto.clave
    form.nombre.data = puesto.nombre
    form.tipo_cargo.data = puesto.tipo_cargo
    form.tipo_empleado.data = puesto.tipo_empleado
    return render_template("puestos/edit.jinja2", form=form, puesto=puesto)


@puestos.route("/puestos/eliminar/<int:puesto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(puesto_id):
    """Eliminar Puesto"""
    puesto = Puesto.query.get_or_404(puesto_id)
    if puesto.estatus == "A":
        puesto.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Puesto {puesto.clave}"),
            url=url_for("puestos.detail", puesto_id=puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("puestos.detail", puesto_id=puesto.id))


@puestos.route("/puestos/recuperar/<int:puesto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(puesto_id):
    """Recuperar Puesto"""
    puesto = Puesto.query.get_or_404(puesto_id)
    if puesto.estatus == "B":
        puesto.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Puesto {puesto.clave}"),
            url=url_for("puestos.detail", puesto_id=puesto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("puestos.detail", puesto_id=puesto.id))
