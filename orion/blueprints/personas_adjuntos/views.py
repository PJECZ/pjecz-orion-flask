"""
Personas Archivos Adjuntos, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import CombinedMultiDict

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from orion.blueprints.bitacoras.models import Bitacora
from orion.blueprints.modulos.models import Modulo
from orion.blueprints.permisos.models import Permiso
from orion.blueprints.usuarios.decorators import permission_required
from orion.blueprints.personas_adjuntos.models import PersonaAdjunto
from orion.blueprints.personas_adjuntos.forms import PersonaAdjuntoForm, PersonaAdjuntoEditForm
from orion.blueprints.personas.models import Persona

from lib.exceptions import (
    MyAnyError,
    MyFilenameError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyUnknownExtensionError,
)
from lib.storage import GoogleCloudStorage

MODULO = "PERSONAS ADJUNTOS"

personas_adjuntos = Blueprint("personas_adjuntos", __name__, template_folder="templates")

SUBDIRECTORIO = "personas_adjuntos"


@personas_adjuntos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_adjuntos.route("/personas_adjuntos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Adjuntos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PersonaAdjunto.query
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
    registros = consulta.order_by(PersonaAdjunto.modificado.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "tipo": PersonaAdjunto.TIPOS[resultado.tipo],
                    "url": url_for("personas_adjuntos.detail", persona_adjunto_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas_adjuntos.route("/personas_adjuntos/<int:persona_adjunto_id>")
def detail(persona_adjunto_id):
    """Detalle de un Adjunto"""
    persona_adjunto = PersonaAdjunto.query.get_or_404(persona_adjunto_id)
    return render_template("personas_adjuntos/detail.jinja2", persona_adjunto=persona_adjunto)


@personas_adjuntos.route("/personas_adjuntos/nuevo_con_persona/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nuevo Archivo Adjunto"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaAdjuntoForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        if request.files["archivo"].filename == "":
            # Guardar datos sin archivo
            adjunto = PersonaAdjunto(
                persona=persona,
                tipo=form.tipo.data,
                descripcion=safe_string(form.descripcion.data, save_enie=True),
            )
            adjunto.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Archivo Adjunto {adjunto.persona.nombre_completo}"),
                url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
        else:
            es_valido = True
            # Guardar cambios con un archivo adjunto
            # Validar archivo
            archivo = request.files["archivo"]
            storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf", "jpg", "jpeg", "png"])
            try:
                storage.set_content_type(archivo.filename)
            except MyNotAllowedExtensionError:
                flash("Tipo de archivo no permitido.", "warning")
                es_valido = False
            except MyUnknownExtensionError:
                flash("Tipo de archivo desconocido.", "warning")
                es_valido = False
            if es_valido:
                # crear un nuevo registro
                adjunto = PersonaAdjunto(
                    persona=persona,
                    tipo=form.tipo.data,
                    descripcion=safe_string(form.descripcion.data, save_enie=True),
                )
                adjunto.save()
                # Subir a Google Cloud Storage
                es_exitoso = True
                try:
                    storage.set_filename(hashed_id=adjunto.encode_id(), description=adjunto.tipo)
                    storage.upload(archivo.stream.read())
                except (MyFilenameError, MyNotAllowedExtensionError, MyUnknownExtensionError):
                    flash("Error fatal al subir el archivo a GCS.", "warning")
                    es_exitoso = False
                except MyMissingConfigurationError:
                    flash("Error al subir el archivo porque falla la configuración de GCS.", "danger")
                    es_exitoso = False
                except Exception:
                    flash("Error desconocido al subir el archivo.", "danger")
                    es_exitoso = False
                # Remplazar archivo
                if es_exitoso:
                    adjunto.archivo = storage.filename
                    adjunto.url = storage.url
                    adjunto.save()
                    # Salida en bitacora
                    bitacora = Bitacora(
                        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                        usuario=current_user,
                        descripcion=safe_message(f"Editado Archivo Adjunto {adjunto.id}"),
                        url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id),
                    )
                    bitacora.save()
                    flash(bitacora.descripcion, "success")
                    return redirect(bitacora.url)
                else:
                    return redirect(url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id))
    # Mostrar valores de los campos
    form.persona.data = persona.nombre_completo
    return render_template("personas_adjuntos/new_with_persona_id.jinja2", form=form, persona=persona)


@personas_adjuntos.route("/personas_adjuntos/edicion/<int:persona_adjunto_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(persona_adjunto_id):
    """Editar Archivo Adjunto"""
    adjunto = PersonaAdjunto.query.get_or_404(persona_adjunto_id)
    form = PersonaAdjuntoEditForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        if request.files["archivo"].filename == "":
            # Guardar cambios sin modificar el archivo
            adjunto.tipo = form.tipo.data
            adjunto.descripcion = safe_string(form.descripcion.data, save_enie=True)
            adjunto.save()
            # Salida en bitacora
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Archivo Adjunto {adjunto.id}"),
                url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
        else:
            es_valido = True
            # Guardar cambios modificando el archivo adjunto
            # Validar archivo
            archivo = request.files["archivo"]
            storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf", "jpg", "jpeg", "png"])
            try:
                storage.set_content_type(archivo.filename)
            except MyNotAllowedExtensionError:
                flash("Tipo de archivo no permitido.", "warning")
                es_valido = False
            except MyUnknownExtensionError:
                flash("Tipo de archivo desconocido.", "warning")
                es_valido = False
            if es_valido:
                # Eliminar y crear un nuevo registro para el rempalzo
                adjunto.delete()
                adjunto_new = PersonaAdjunto(
                    persona=adjunto.persona,
                    tipo=form.tipo.data,
                    descripcion=safe_string(form.descripcion.data, save_enie=True),
                )
                adjunto_new.save()
                # Subir a Google Cloud Storage
                es_exitoso = True
                try:
                    storage.set_filename(hashed_id=adjunto_new.encode_id(), description=adjunto_new.tipo)
                    storage.upload(archivo.stream.read())
                except (MyFilenameError, MyNotAllowedExtensionError, MyUnknownExtensionError):
                    flash("Error fatal al subir el archivo a GCS.", "warning")
                    es_exitoso = False
                except MyMissingConfigurationError:
                    flash("Error al subir el archivo porque falla la configuración de GCS.", "danger")
                    es_exitoso = False
                except Exception:
                    flash("Error desconocido al subir el archivo.", "danger")
                    es_exitoso = False
                # Remplazar archivo
                if es_exitoso:
                    adjunto_new.archivo = storage.filename
                    adjunto_new.url = storage.url
                    adjunto_new.save()
                    # Salida en bitacora
                    bitacora = Bitacora(
                        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                        usuario=current_user,
                        descripcion=safe_message(f"Editado Archivo Adjunto {adjunto_new.id}, se dio de baja {adjunto.id}"),
                        url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto_new.id),
                    )
                    bitacora.save()
                    flash(bitacora.descripcion, "success")
                    return redirect(bitacora.url)
                else:
                    adjunto_new.delete()
                    adjunto.recover()
                    return redirect(url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id))
    form.persona.data = adjunto.persona.nombre_completo
    form.tipo.data = adjunto.tipo
    form.descripcion.data = adjunto.descripcion
    return render_template("personas_adjuntos/edit.jinja2", form=form, persona_adjunto=adjunto)


@personas_adjuntos.route("/personas_adjuntos/eliminar/<int:persona_adjunto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(persona_adjunto_id):
    """Eliminar Archivo Adjunto"""
    adjunto = PersonaAdjunto.query.get_or_404(persona_adjunto_id)
    if adjunto.estatus == "A":
        adjunto.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Archivo Adjunto {adjunto.persona.nombre_completo}"),
            url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id))


@personas_adjuntos.route("/personas_adjuntos/recuperar/<int:persona_adjunto_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(persona_adjunto_id):
    """Recuperar Archivo Adjunto"""
    adjunto = PersonaAdjunto.query.get_or_404(persona_adjunto_id)
    if adjunto.estatus == "B":
        adjunto.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Archivo Adjunto {adjunto.persona.nombre_completo}"),
            url=url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_adjuntos.detail", persona_adjunto_id=adjunto.id))
