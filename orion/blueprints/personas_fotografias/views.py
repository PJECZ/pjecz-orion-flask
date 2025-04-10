"""
Personas Fotografías, vistas
"""

import json
from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.exceptions import NotFound

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.exceptions import MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError, MyUploadError
from lib.google_cloud_storage import get_blob_name_from_url, get_file_from_gcs, upload_file_to_gcs
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


@personas_fotografias.route("/personas_fotografias/<int:persona_fotografia_id>/img")
def download_img(persona_fotografia_id):
    """Descargar el archivo PDF de un Archivo"""

    # Consultar
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)

    # Si el estatus es B, no se puede descargar
    if fotografia.estatus == "B":
        flash("No se puede descargar un archivo inactivo", "warning")
        return redirect(url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id))

    # Tomar el nombre del archivo con el que sera descargado
    descarga_nombre = fotografia.archivo

    # Obtener el contenido del archivo desde Google Storage
    try:
        descarga_contenido = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(fotografia.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        flash(str(error), "danger")
        return redirect(url_for("personas_fotografias.detail", persona_fotografia_id=fotografia.id))

    # Descargar un archivo PDF
    response = make_response(descarga_contenido)
    response.headers["Content-Type"] = "image/jpg"
    response.headers["Content-Disposition"] = f"attachment; filename={descarga_nombre}"
    return response


@personas_fotografias.route("/personas_fotografias/ver_archivo_img/<int:persona_fotografia_id>")
def view_file_img(persona_fotografia_id):
    """Ver archivo IMG de PersonaFotografia para insertarlo en un iframe en el detalle"""

    # Consultar
    fotografia = PersonaFotografia.query.get_or_404(persona_fotografia_id)

    # Obtener el contenido del archivo
    try:
        archivo = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(fotografia.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        print(fotografia.url)
        raise NotFound("No se encontró el archivo.")

    # Entregar el archivo
    response = make_response(archivo)
    response.headers["Content-Type"] = "image/jpg"
    return response
