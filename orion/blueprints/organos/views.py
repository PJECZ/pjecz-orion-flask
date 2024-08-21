"""
Órganos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_clave

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.organos.forms import OrganoForm
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.organos.models import Organo

MODULO = "ORGANOS"

organos = Blueprint("organos", __name__, template_folder="templates")


@organos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@organos.route("/organos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Organos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Organo.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(Organo.clave.contains(clave))
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"])
        if nombre != "":
            consulta = consulta.filter(Organo.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Organo.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("organos.detail", organo_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@organos.route("/organos")
def list_active():
    """Listado de Órganos activos"""
    return render_template(
        "organos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Órganos",
        estatus="A",
    )


@organos.route("/organos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Órganos inactivos"""
    return render_template(
        "organos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Órganos inactivos",
        estatus="B",
    )


@organos.route("/organos/<int:organo_id>")
def detail(organo_id):
    """Detalle de un Órgano"""
    organo = Organo.query.get_or_404(organo_id)
    return render_template("organos/detail.jinja2", organo=organo)


@organos.route("/organos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Órgano"""
    form = OrganoForm()
    if form.validate_on_submit():
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if Organo.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("organos/new.jinja2", form=form)
        # Guardar
        organo = Organo(
            clave=clave,
            nombre=safe_string(form.nombre.data),
        )
        organo.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Órgano {organo.clave}"),
            url=url_for("organos.detail", organo_id=organo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("organos/new.jinja2", form=form)


@organos.route("/organos/edicion/<int:organo_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(organo_id):
    """Editar Órgano"""
    organo = Organo.query.get_or_404(organo_id)
    form = OrganoForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if organo.clave != clave:
            carrera_existente = Organo.query.filter_by(clave=clave).first()
            if carrera_existente and carrera_existente.id != organo.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            organo.clave = clave
            organo.nombre = safe_string(form.nombre.data)
            organo.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Órgano {organo.clave}"),
                url=url_for("organos.detail", organo_id=organo.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = organo.clave
    form.nombre.data = organo.nombre
    return render_template("organos/edit.jinja2", form=form, organo=organo)


@organos.route("/organos/eliminar/<int:organo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(organo_id):
    """Eliminar Órgano"""
    organo = Organo.query.get_or_404(organo_id)
    if organo.estatus == "A":
        organo.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Órgano {organo.clave}"),
            url=url_for("organos.detail", organo_id=organo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("organos.detail", organo_id=organo.id))


@organos.route("/organos/recuperar/<int:organo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(organo_id):
    """Recuperar Órgano"""
    organo = Organo.query.get_or_404(organo_id)
    if organo.estatus == "B":
        organo.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Órgano {organo.clave}"),
            url=url_for("organos.detail", organo_id=organo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("organos.detail", organo_id=organo.id))


@organos.route("/organos/query_organos_json", methods=["POST"])
def query_organos_json():
    """Proporcionar el JSON de Órganos para elegir en un Select2"""
    consulta = Organo.query.filter_by(estatus="A")
    if "clave_nombre" in request.form:
        clave_nombre = safe_string(request.form["clave_nombre"]).upper()
        if clave_nombre != "":
            consulta = consulta.filter(or_(Organo.clave.contains(clave_nombre), Organo.nombre.contains(clave_nombre)))
    results = []
    for centro_trabajo in consulta.order_by(Organo.id).limit(15).all():
        results.append(
            {
                "id": centro_trabajo.id,
                "text": centro_trabajo.nombre_descriptivo,
            }
        )
    return {"results": results, "pagination": {"more": False}}
