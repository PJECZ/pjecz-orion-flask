"""
Domicilios, vistas
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
from orion.blueprints.domicilios.models import Domicilio
from orion.blueprints.domicilios.forms import DomicilioForm
from orion.blueprints.personas.models import Persona

MODULO = "DOMICILIOS"

domicilios = Blueprint("domicilios", __name__, template_folder="templates")


@domicilios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@domicilios.route("/domicilios/<int:domicilio_id>")
def detail(domicilio_id):
    """Detalle de un Domicilio"""
    domicilio = Domicilio.query.get_or_404(domicilio_id)
    return render_template("domicilios/detail.jinja2", domicilio=domicilio)


@domicilios.route("/domicilios/<int:persona_id>")
def detail_with_persona_id(persona_id):
    """Detalle de un Domicilio de una Persona"""
    domicilio = Domicilio.query.filter(persona_id=persona_id).first()
    return render_template("domicilios/detail.jinja2", domicilio=domicilio)


# NEW TODO:


@domicilios.route("/domicilios/edicion/<int:persona_id>/<int:domicilio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(persona_id, domicilio_id):
    """Editar Domicilio"""
    persona = Persona.query.get_or_404(persona_id)
    domicilio = Domicilio.query.get_or_404(domicilio_id)
    form = DomicilioForm()
    if form.validate_on_submit():
        domicilio.calle = safe_string(form.calle.data, save_enie=True)
        domicilio.num_ext = safe_string(form.numero_exterior.data)
        domicilio.num_int = safe_string(form.numero_interior.data)
        domicilio.colonia = safe_string(form.colonia.data, save_enie=True)
        domicilio.municipio = safe_string(form.municipio.data, save_enie=True)
        domicilio.estado = safe_string(form.estado.data, save_enie=True)
        domicilio.pais = safe_string(form.pais.data, save_enie=True)
        domicilio.cp = form.codigo_postal.data
        domicilio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Domicilio de {persona.nombre_completo}"),
            url=url_for("domicilios.detail", domicilio_id=domicilio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("personas.detail_section", seccion="domicilios", persona_id=persona.id))
    form.persona.data = persona.nombre_completo
    form.calle.data = domicilio.calle
    form.numero_exterior.data = domicilio.num_ext
    form.numero_interior.data = domicilio.num_int
    form.colonia.data = domicilio.colonia
    form.municipio.data = domicilio.municipio
    form.estado.data = domicilio.estado
    form.pais.data = domicilio.pais
    form.codigo_postal.data = domicilio.cp
    return render_template("domicilios/edit.jinja2", form=form, persona=persona, domicilio=domicilio)


@domicilios.route("/domicilios/eliminar/<int:domicilio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(domicilio_id):
    """Eliminar Domicilio"""
    domicilio = Domicilio.query.get_or_404(domicilio_id)
    if domicilio.estatus == "A":
        domicilio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Domicilio {domicilio.id}"),
            url=url_for("domicilios.detail", domicilio_id=domicilio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("domicilios.detail", domicilio_id=domicilio.id))


@domicilios.route("/domicilios/recuperar/<int:domicilio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(domicilio_id):
    """Recuperar Domicilio"""
    domicilio = Domicilio.query.get_or_404(domicilio_id)
    if domicilio.estatus == "B":
        domicilio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Domicilio {domicilio.id}"),
            url=url_for("domicilios.detail", domicilio_id=domicilio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("domicilios.detail", domicilio_id=domicilio.id))
