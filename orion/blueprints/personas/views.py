"""
Personas, vistas
"""

import json
import locale
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string, safe_curp, safe_rfc, safe_email
from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.personas.models import Persona
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.personas_domicilios.models import PersonaDomicilio
from orion.blueprints.personas_fotografias.models import PersonaFotografia
from orion.blueprints.personas.forms import (
    PersonaEditDomicilioFiscalForm,
    PersonaEditDatosAcademicosForm,
    PersonaEditDatosPersonalesForm,
    PersonaEditDatosGeneralesForm,
    PersonaEditObservacionesForm,
)

MODULO = "PERSONAS"

personas = Blueprint("personas", __name__, template_folder="templates")


@personas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas.route("/personas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Personas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Persona.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "numero_empleado" in request.form:
        try:
            numero_empleado = int(request.form["numero_empleado"])
            consulta = consulta.filter_by(numero_empleado=numero_empleado)
        except ValueError:
            pass
    if "nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["nombre_completo"])
        if nombre_completo != "":
            for palabra in nombre_completo.split(" "):
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    if "situacion" in request.form:
        consulta = consulta.filter_by(situacion=request.form["situacion"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(Persona.modificado.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "numero_empleado": resultado.numero_empleado,
                "detalle": {
                    "nombre_completo": resultado.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.id),
                },
                "situacion": {
                    "nombre": resultado.situacion,
                    "descripcion": Persona.SITUACIONES[resultado.situacion],
                },
                "sexo": "HOMBRE" if resultado.sexo == "H" else "MUJER",
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas.route("/personas")
def list_active():
    """Listado de Personas activos"""
    return render_template(
        "personas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Personas",
        situaciones=Persona.SITUACIONES,
        estatus="A",
    )


@personas.route("/personas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Personas inactivos"""
    return render_template(
        "personas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Personas inactivos",
        situaciones=Persona.SITUACIONES,
        estatus="B",
    )


@personas.route("/personas/<int:persona_id>")
def detail(persona_id):
    """Detalle de un Persona"""
    locale.setlocale(locale.LC_TIME, "es_MX")
    persona = Persona.query.get_or_404(persona_id)
    fotografia = (
        PersonaFotografia.query.filter_by(persona=persona)
        .filter_by(estatus="A")
        .order_by(PersonaFotografia.modificado.desc())
        .first()
    )
    return render_template("personas/detail.jinja2", persona=persona, fotografia=fotografia)


@personas.route("/personas/<string:seccion>/<int:persona_id>")
def detail_section(seccion, persona_id):
    """Detalle de un Persona"""
    locale.setlocale(locale.LC_TIME, "es_MX")
    persona = Persona.query.get_or_404(persona_id)
    fotografia = (
        PersonaFotografia.query.filter_by(persona=persona)
        .filter_by(estatus="A")
        .order_by(PersonaFotografia.modificado.desc())
        .first()
    )
    seccion_page = f"personas/detail_{seccion}.jinja2"
    # Calculo de edad para la sección de Datos Personales
    edad = 0
    if persona.fecha_nacimiento:
        edad = date.today() - persona.fecha_nacimiento
        edad = int(edad.days / 365)
    if seccion == "domicilios":
        persona_domicilio = (
            PersonaDomicilio.query.filter_by(persona_id=persona_id)
            .filter_by(estatus="A")
            .order_by(PersonaDomicilio.modificado.desc())
            .first()
        )
        if persona_domicilio:
            return render_template(seccion_page, persona=persona, fotografia=fotografia, domicilio=persona_domicilio.domicilio)
        return render_template(seccion_page, persona=persona, fotografia=fotografia, domicilio=None)
    return render_template(seccion_page, persona=persona, fotografia=fotografia, edad=edad)


@personas.route("/personas/edicion_domicilio_fiscal/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit_domicilio_fiscal(persona_id):
    """Editar Domicilio Fiscal de una Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaEditDomicilioFiscalForm()
    if form.validate_on_submit():
        persona.domicilio_fiscal_calle = safe_string(form.calle.data, save_enie=True)
        persona.domicilio_fiscal_numero_exterior = safe_string(form.numero_exterior.data)
        persona.domicilio_fiscal_numero_interior = safe_string(form.numero_interior.data)
        persona.domicilio_fiscal_colonia = safe_string(form.colonia.data, save_enie=True)
        persona.domicilio_fiscal_municipio = safe_string(form.municipio.data, save_enie=True)
        persona.domicilio_fiscal_estado = safe_string(form.estado.data, save_enie=True)
        persona.domicilio_fiscal_localidad = safe_string(form.localidad.data, save_enie=True)
        persona.domicilio_fiscal_cp = form.codigo_postal.data
        persona.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Domicilio Fiscal de una Persona {persona.nombre_completo}"),
            url=url_for("personas.detail", persona_id=persona.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("personas.detail_section", seccion="domicilios", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    form.calle.data = persona.domicilio_fiscal_calle
    form.numero_exterior.data = persona.domicilio_fiscal_numero_exterior
    form.numero_interior.data = persona.domicilio_fiscal_numero_interior
    form.colonia.data = persona.domicilio_fiscal_colonia
    form.municipio.data = persona.domicilio_fiscal_municipio
    form.estado.data = persona.domicilio_fiscal_estado
    form.localidad.data = persona.domicilio_fiscal_localidad
    form.codigo_postal.data = persona.domicilio_fiscal_cp
    return render_template("personas/edit_domicilio_fiscal.jinja2", form=form, persona=persona)


@personas.route("/personas/edicion_datos_academicos/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit_datos_academicos(persona_id):
    """Editar Domicilio Fiscal de una Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaEditDatosAcademicosForm()
    if form.validate_on_submit():
        persona.nivel_estudios = form.nivel_estudios.data
        persona.nivel_estudios_max_id = form.nivel_max_estudios.data
        persona.carrera_id = form.carrera.data
        persona.cedula_profesional = form.cedula_profesional.data
        persona.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Datos Académicos de una Persona {persona.nombre_completo}"),
            url=url_for("personas.detail", persona_id=persona.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("personas.detail_section", seccion="historial_academico", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    form.nivel_estudios.data = persona.nivel_estudios
    form.nivel_max_estudios.data = persona.nivel_estudios_max_id
    form.carrera.data = persona.carrera_id
    form.cedula_profesional.data = persona.cedula_profesional
    return render_template("personas/edit_datos_academicos.jinja2", form=form, persona=persona)


@personas.route("/personas/edicion_datos_personales/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit_datos_personales(persona_id):
    """Editar Domicilio Fiscal de una Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaEditDatosPersonalesForm()
    if form.validate_on_submit():
        persona.fecha_ingreso_gobierno = form.fecha_ingreso_gob.data
        persona.fecha_ingreso_pj = form.fecha_ingreso_pj.data
        persona.num_seguridad_social = safe_string(form.num_seguridad_social.data)
        persona.estado_civil = form.estado_civil.data
        persona.fecha_nacimiento = form.fecha_nacimiento.data
        persona.telefono_personal = form.telefono_personal.data
        persona.email_secundario = form.email_secundario.data
        persona.madre = form.es_madre.data
        persona.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Datos Personales de una Persona {persona.nombre_completo}"),
            url=url_for("personas.detail", persona_id=persona.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("personas.detail_section", seccion="datos_personales", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    form.fecha_ingreso_gob.data = persona.fecha_ingreso_gobierno
    form.fecha_ingreso_pj.data = persona.fecha_ingreso_pj
    form.num_seguridad_social.data = persona.num_seguridad_social
    form.estado_civil.data = persona.estado_civil
    form.fecha_nacimiento.data = persona.fecha_nacimiento
    form.telefono_personal.data = persona.telefono_personal
    form.telefono_domicilio.data = persona.telefono_domicilio
    form.email_secundario.data = persona.email_secundario
    form.es_madre.data = persona.madre
    return render_template("personas/edit_datos_personales.jinja2", form=form, persona=persona)


@personas.route("/personas/edicion_datos_generales/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit_datos_generales(persona_id):
    """Editar Domicilio Fiscal de una Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaEditDatosGeneralesForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar
        rfc = None
        try:
            rfc = safe_rfc(form.rfc.data)
        except:
            flash("RFC no válido", "warning")
            es_valido = False
        curp = None
        try:
            curp = safe_curp(form.curp.data)
        except:
            flash("CURP no válido", "warning")
            es_valido = False

        if es_valido:
            # Guardar Cambios
            persona.nombres = safe_string(form.nombres.data, save_enie=True)
            persona.apellido_primero = safe_string(form.apellido_primero.data, save_enie=True)
            persona.apellido_segundo = safe_string(form.apellido_segundo.data, save_enie=True)
            persona.sexo = form.sexo.data
            persona.rfc = rfc
            persona.curp = curp
            persona.email = safe_email(form.email.data)
            persona.telefono_trabajo = safe_string(form.telefono_trabajo.data)
            persona.telefono_trabajo_extension = safe_string(form.telefono_trabajo_extension.data)
            persona.situancion = form.situacion.data
            persona.fecha_baja = form.fecha_baja.data
            persona.numero_empleado = form.numero_empleado.data
            persona.falta_papeleria = form.falta_papeleria.data
            persona.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Datos Generales de una Persona {persona.nombre_completo}"),
                url=url_for("personas.detail", persona_id=persona.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("personas.detail_section", seccion="datos_generales", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    form.nombres.data = persona.nombres
    form.apellido_primero.data = persona.apellido_primero
    form.apellido_segundo.data = persona.apellido_segundo
    form.sexo.data = persona.sexo
    form.rfc.data = persona.rfc
    form.curp.data = persona.curp
    form.email.data = persona.email
    form.telefono_trabajo.data = persona.telefono_trabajo
    form.telefono_trabajo_extension.data = persona.telefono_trabajo_extension
    form.situacion.data = persona.situacion
    form.fecha_baja.data = persona.fecha_baja
    form.numero_empleado.data = persona.numero_empleado
    form.falta_papeleria.data = persona.falta_papeleria
    return render_template("personas/edit_datos_generales.jinja2", form=form, persona=persona)


@personas.route("/personas/edicion_observaciones/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit_observaciones(persona_id):
    """Editar Domicilio Fiscal de una Persona"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaEditObservacionesForm()
    if form.validate_on_submit():
        persona.observaciones = safe_string(form.observaciones.data, save_enie=True)
        persona.observaciones_especiales = safe_string(form.observaciones_especiales.data, save_enie=True)
        persona.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Observaciones de una Persona {persona.nombre_completo}"),
            url=url_for("personas.detail", persona_id=persona.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("personas.detail_section", seccion="observaciones", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    form.observaciones.data = persona.observaciones
    form.observaciones_especiales.data = persona.observaciones_especiales
    return render_template("personas/edit_observaciones.jinja2", form=form, persona=persona)


@personas.route("/personas/query_personas_json", methods=["POST"])
def query_personas_json():
    """Proporcionar el JSON de Persona para elegir en un Select2"""
    consulta = Persona.query.filter_by(estatus="A")
    if "nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["nombre_completo"]).upper()
        if nombre_completo != "":
            palabras = nombre_completo.split()
            for palabra in palabras:
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    results = []
    for persona in consulta.order_by(Persona.id).limit(15).all():
        results.append(
            {
                "id": persona.id,
                "text": persona.nombre_completo,
            }
        )
    return {"results": results, "pagination": {"more": False}}
