"""
Personas Fotografías, vistas
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
from orion.blueprints.personas_fotografias.models import PersonaFotografia
from orion.blueprints.personas_fotografias.forms import PersonaFotografiaForm
from orion.blueprints.personas.models import Persona

from lib.exceptions import (
    MyAnyError,
    MyFilenameError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyUnknownExtensionError,
)
from lib.storage import GoogleCloudStorage

MODULO = "PERSONAS FOTOGRAFIAS"

personas_fotografias = Blueprint("personas_fotografias", __name__, template_folder="templates")

SUBDIRECTORIO = "personas_fotografias"


@personas_fotografias.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_fotografias.route("/personas_fotografias/<int:persona_fotografia_id>")
def detail(persona_fotografia_id):
    """Detalle de un Fotografía"""
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)
    return render_template("personas_fotografias/detail.jinja2", fotografia=fotografia)


# NEW_WITH_PERSONA_ID TODO:
@personas_fotografias.route("/personas_fotografias/nuevo_con_persona/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nuevo Fotografía"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaFotografiaForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        es_valido = True
        archivo = request.files["archivo"]
        storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["jpg", "jpeg", "png"])
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
            fotografia = PersonaFotografia(
                persona=persona,
                archivo="",
                url="",
            )
            fotografia.save()
            # Subir a Google Cloud Storage
            es_exitoso = True
            try:
                storage.set_filename(hashed_id=fotografia.encode_id(), description="fotografia")
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
                fotografia.archivo = storage.filename
                fotografia.url = storage.url
                fotografia.save()
                # Salida en bitacora
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Nueva fotografia {fotografia.id}"),
                    url=url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(url_for("personas.detail", persona_id=persona_id))
            else:
                fotografia.delete()
                return redirect(url_for("personas.detail", persona_id=persona_id))
    form.persona.data = persona.nombre_completo
    return render_template("personas_fotografias/new_with_persona_id.jinja2", form=form, persona=persona)


@personas_fotografias.route("/personas_fotografias/edicion/<int:persona_fotografia_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(persona_fotografia_id):
    """Editar Fotografía"""
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)
    form = PersonaFotografiaForm()
    if form.validate_on_submit():
        es_valido = True
        archivo = request.files["archivo"]
        storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["jpg", "jpeg", "png"])
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
            fotografia_new = PersonaFotografia(
                persona=fotografia.persona,
                archivo="",
                url="",
            )
            fotografia_new.save()
            # Subir a Google Cloud Storage
            es_exitoso = True
            try:
                storage.set_filename(hashed_id=fotografia_new.encode_id(), description="fotografia")
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
                fotografia.delete()
                fotografia_new.archivo = storage.filename
                fotografia_new.url = storage.url
                fotografia_new.save()
                # Salida en bitacora
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Editado Fotografía {fotografia_new.persona.nombre_completo}"),
                    url=url_for("personas_fotografias.detail", persona_fotografia_id=fotografia_new.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
            else:
                fotografia_new.delete()
                return redirect(url_for("personas.detail", persona_id=fotografia.persona_id))
    form.persona.data = fotografia.persona.nombre_completo
    return render_template("personas_fotografias/edit.jinja2", form=form, fotografia=fotografia)


@personas_fotografias.route("/personas_fotografias/eliminar/<int:persona_fotografia_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(persona_fotografia_id):
    """Eliminar Fotografía"""
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)
    if fotografia.estatus == "A":
        fotografia.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Fotografía {fotografia.persona.nombre_completo}"),
            url=url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id))


@personas_fotografias.route("/personas_fotografias/recuperar/<int:persona_fotografia_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(persona_fotografia_id):
    """Recuperar Fotografía"""
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)
    if fotografia.estatus == "B":
        fotografia.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Fotografía {fotografia.persona.nombre_completo}"),
            url=url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id))
