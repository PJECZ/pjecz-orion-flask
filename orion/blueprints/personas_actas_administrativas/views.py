"""
Persona Actas Administrativas, vistas
"""

import json
from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
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
from orion.blueprints.personas_actas_administrativas.models import PersonaActaAdministrativa
from orion.blueprints.personas_actas_administrativas.forms import PersonaActaAdministrativaForm
from orion.blueprints.personas.models import Persona

from lib.exceptions import (
    MyAnyError,
    MyFilenameError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyUnknownExtensionError,
)
from lib.storage import GoogleCloudStorage

MODULO = "PERSONAS ACTAS ADMINISTRATIVAS"

personas_actas_administrativas = Blueprint("personas_actas_administrativas", __name__, template_folder="templates")

SUBDIRECTORIO = "actas_administrativas"


@personas_actas_administrativas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_actas_administrativas.route("/personas_actas_administrativas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Personas Acta Administrativa"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PersonaActaAdministrativa.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(PersonaActaAdministrativa.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(PersonaActaAdministrativa.estatus == "A")
    if "id" in request.form:
        consulta = consulta.filter(PersonaActaAdministrativa.id == request.form["id"])
    # Luego filtrar por columnas de otras tablas
    if "persona_nombre_completo" in request.form:
        nombre_completo = safe_string(request.form["persona_nombre_completo"])
        if nombre_completo != "":
            consulta = consulta.join(Persona)
            for palabra in nombre_completo.split(" "):
                consulta = consulta.filter(
                    or_(
                        Persona.nombres.contains(palabra),
                        Persona.apellido_primero.contains(palabra),
                        Persona.apellido_segundo.contains(palabra),
                    )
                )
    if "persona_id" in request.form:
        consulta = consulta.join(Persona)
        consulta = consulta.filter(Persona.id == request.form["persona_id"])
    # Ordenar y paginar
    registros = consulta.order_by(PersonaActaAdministrativa.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=resultado.id),
                },
                "persona": {
                    "nombre": resultado.persona.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.persona.id),
                },
                "fecha": resultado.fecha.strftime("%Y-%m-%d"),
                "falta": resultado.falta,
                "sancion": resultado.sancion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas_actas_administrativas.route("/personas_actas_administrativas")
def list_active():
    """Listado de Actas Administrativas activos"""
    return render_template(
        "personas_actas_administrativas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Actas Administrativas",
        estatus="A",
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Actas Administrativas inactivos"""
    return render_template(
        "personas_actas_administrativas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Actas Administrativas inactivos",
        estatus="B",
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/<int:persona_acta_administrativa_id>")
def detail(persona_acta_administrativa_id):
    """Detalle de un Persona Acta Administrativa"""
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)
    return render_template(
        "personas_actas_administrativas/detail.jinja2", persona_acta_administrativa=persona_acta_administrativa
    )


@personas_actas_administrativas.route(
    "/personas_actas_administrativas/nuevo_con_persona/<int:persona_id>", methods=["GET", "POST"]
)
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nuevo Acta Administrativa"""
    persona = Persona.query.get_or_404(persona_id)
    form = PersonaActaAdministrativaForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        # Guardar datos sin archivo
        if request.files["archivo"].filename == "":
            persona_acta_administrativa = PersonaActaAdministrativa(
                persona=persona,
                fecha=form.fecha.data,
                falta=safe_string(form.falta.data),
                sancion=safe_string(form.sancion.data),
            )
            persona_acta_administrativa.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Acta Administrativa {persona_acta_administrativa.fecha}"),
                url=url_for(
                    "personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id
                ),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
        else:
            # Guardar cambios con un archivo adjunto
            # Validaciones
            es_valido = True
            # Validar archivo
            archivo = request.files["archivo"]
            storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf"])
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
                persona_acta_administrativa = PersonaActaAdministrativa(
                    persona=persona,
                    fecha=form.fecha.data,
                    falta=safe_string(form.falta.data),
                    sancion=safe_string(form.sancion.data),
                )
                persona_acta_administrativa.save()
                # Subir a Google Cloud Storage
                es_exitoso = True
                try:
                    storage.set_filename(hashed_id=persona_acta_administrativa.encode_id(), description="ACTA-ADMINISTRATIVA")
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
                    persona_acta_administrativa.archivo = storage.filename
                    persona_acta_administrativa.url = storage.url
                    persona_acta_administrativa.save()
                    # Salida en bitacora
                    bitacora = Bitacora(
                        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                        usuario=current_user,
                        descripcion=safe_message(f"Nueva Acta Administrativa {persona_acta_administrativa.id}"),
                        url=url_for(
                            "personas_actas_administrativas.detail",
                            persona_acta_administrativa_id=persona_acta_administrativa.id,
                        ),
                    )
                    bitacora.save()
                    flash(bitacora.descripcion, "success")
                    return redirect(bitacora.url)
                else:
                    return redirect(
                        url_for(
                            "personas_actas_administrativas.detail",
                            persona_acta_administrativa_id=persona_acta_administrativa.id,
                        )
                    )
    # Mostrar valores de los campos
    form.persona.data = persona.nombre_completo
    return render_template("personas_actas_administrativas/new_with_persona_id.jinja2", form=form, persona=persona)


@personas_actas_administrativas.route(
    "/personas_actas_administrativas/edicion/<int:persona_acta_administrativa_id>", methods=["GET", "POST"]
)
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(persona_acta_administrativa_id):
    """Editar Acta Administrativa"""
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)
    form = PersonaActaAdministrativaForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        # Guardar cambios sin modificar el archivo
        if request.files["archivo"].filename == "":
            persona_acta_administrativa.fecha = form.fecha.data
            persona_acta_administrativa.falta = safe_string(form.falta.data)
            persona_acta_administrativa.sancion = safe_string(form.sancion.data)
            persona_acta_administrativa.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Acta Administrativa {persona_acta_administrativa.id}"),
                url=url_for(
                    "personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id
                ),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
        else:
            # Guardar cambios modificando el archivo adjunto
            es_valido = True
            # Validar archivo
            archivo = request.files["archivo"]
            storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf"])
            try:
                storage.set_content_type(archivo.filename)
            except MyNotAllowedExtensionError:
                flash("Tipo de archivo no permitido.", "warning")
                es_valido = False
            except MyUnknownExtensionError:
                flash("Tipo de archivo desconocido.", "warning")
                es_valido = False
            if es_valido:
                # Eliminar y crear un nuevo registro para el remplazo
                persona_acta_administrativa.delete()
                # Crear nuevo registro
                persona_acta_administrativa_new = PersonaActaAdministrativa(
                    persona=persona_acta_administrativa.persona,
                    fecha=form.fecha.data,
                    falta=safe_string(form.falta.data),
                    sancion=safe_string(form.sancion.data),
                )
                persona_acta_administrativa_new.save()
                # Subir a Google Cloud Storage
                es_exitoso = True
                try:
                    storage.set_filename(
                        hashed_id=persona_acta_administrativa_new.encode_id(), description="ACTA-ADMINISTRATIVA"
                    )
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
                    persona_acta_administrativa_new.archivo = storage.filename
                    persona_acta_administrativa_new.url = storage.url
                    persona_acta_administrativa_new.save()
                    # Salida en bitacora
                    bitacora = Bitacora(
                        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                        usuario=current_user,
                        descripcion=safe_message(
                            f"Editado Acta Administrativa {persona_acta_administrativa_new.id}, se dio de baja {persona_acta_administrativa.id}"
                        ),
                        url=url_for(
                            "personas_actas_administrativas.detail",
                            persona_acta_administrativa_id=persona_acta_administrativa_new.id,
                        ),
                    )
                    bitacora.save()
                    flash(bitacora.descripcion, "success")
                    return redirect(bitacora.url)
                else:
                    persona_acta_administrativa_new.delete()
                    persona_acta_administrativa.recover()
                    return redirect(
                        url_for(
                            "personas_actas_administrativas.detail",
                            persona_acta_administrativa_id=persona_acta_administrativa.id,
                        )
                    )
    form.persona.data = persona_acta_administrativa.persona.nombre_completo
    form.fecha.data = persona_acta_administrativa.fecha
    form.falta.data = persona_acta_administrativa.falta
    form.sancion.data = persona_acta_administrativa.sancion
    return render_template(
        "personas_actas_administrativas/edit.jinja2", form=form, persona_acta_administrativa=persona_acta_administrativa
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/eliminar/<int:persona_acta_administrativa_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(persona_acta_administrativa_id):
    """Eliminar Acta Administrativa"""
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)
    if persona_acta_administrativa.estatus == "A":
        persona_acta_administrativa.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Acta Administrativa {persona_acta_administrativa.id}"),
            url=url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(
        url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id)
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/recuperar/<int:persona_acta_administrativa_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(persona_acta_administrativa_id):
    """Recuperar Acta Administrativa"""
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)
    if persona_acta_administrativa.estatus == "B":
        persona_acta_administrativa.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Acta Administrativa {persona_acta_administrativa.id}"),
            url=url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(
        url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id)
    )


@personas_actas_administrativas.route("/personas_actas_administrativas/<int:persona_acta_administrativa_id>/pdf")
def download_pdf(persona_acta_administrativa_id):
    """Descargar el archivo PDF de un Archivo"""

    # Consultar
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)

    # Si el estatus es B, no se puede descargar
    if persona_acta_administrativa.estatus == "B":
        flash("No se puede descargar un archivo inactivo", "warning")
        return redirect(
            url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id)
        )

    # Tomar el nombre del archivo con el que sera descargado
    descarga_nombre = persona_acta_administrativa.archivo

    # Obtener el contenido del archivo desde Google Storage
    try:
        descarga_contenido = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(persona_acta_administrativa.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        flash(str(error), "danger")
        return redirect(
            url_for("personas_actas_administrativas.detail", persona_acta_administrativa_id=persona_acta_administrativa.id)
        )

    # Descargar un archivo PDF
    response = make_response(descarga_contenido)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={descarga_nombre}"
    return response


@personas_actas_administrativas.route("/personas_actas_administrativas/ver_archivo_pdf/<int:persona_acta_administrativa_id>")
def view_file_pdf(persona_acta_administrativa_id):
    """Ver archivo PDF de PersonaActaAdministrativa para insertarlo en un iframe en el detalle"""

    # Consultar
    persona_acta_administrativa = PersonaActaAdministrativa.query.get_or_404(persona_acta_administrativa_id)

    # Obtener el contenido del archivo
    try:
        archivo = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(persona_acta_administrativa.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        print(persona_acta_administrativa.url)
        raise NotFound("No se encontró el archivo.")

    # Entregar el archivo
    response = make_response(archivo)
    response.headers["Content-Type"] = "application/pdf"
    return response
