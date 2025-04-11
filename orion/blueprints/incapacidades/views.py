"""
Incapacidades, vistas
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
from orion.blueprints.incapacidades.models import Incapacidad
from orion.blueprints.personas.models import Persona
from orion.blueprints.incapacidades.forms import IncapacidadForm, IncapacidadWithPersonaForm
from orion.blueprints.historial_puestos.models import HistorialPuesto

from lib.exceptions import (
    MyAnyError,
    MyFilenameError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyUnknownExtensionError,
)
from lib.storage import GoogleCloudStorage

MODULO = "INCAPACIDADES"

incapacidades = Blueprint("incapacidades", __name__, template_folder="templates")

SUBDIRECTORIO = "incapacidades"


@incapacidades.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@incapacidades.route("/incapacidades/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Incapacidades"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Incapacidad.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(Incapacidad.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(Incapacidad.estatus == "A")
    if "fecha_inicio" in request.form:
        consulta = consulta.filter(Incapacidad.fecha_inicio >= request.form["fecha_inicio"])
    if "fecha_termino" in request.form:
        consulta = consulta.filter(Incapacidad.fecha_termino <= request.form["fecha_termino"])
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
    registros = consulta.order_by(Incapacidad.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "periodo": resultado.fecha_inicio.strftime("%Y-%m-%d")
                    + " — "
                    + resultado.fecha_termino.strftime("%Y-%m-%d"),
                    "url": url_for("incapacidades.detail", incapacidad_id=resultado.id),
                },
                "persona": {
                    "nombre": resultado.persona.nombre_completo,
                    "url": url_for("personas.detail", persona_id=resultado.persona.id),
                },
                "dias": f"{(resultado.fecha_termino - resultado.fecha_inicio).days + 1} DÍAS",
                "motivo": resultado.motivo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@incapacidades.route("/incapacidades")
def list_active():
    """Listado de Incapacidades activos"""
    return render_template(
        "incapacidades/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Incapacidades",
        estatus="A",
    )


@incapacidades.route("/incapacidades/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Incapacidades inactivos"""
    return render_template(
        "incapacidades/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Incapacidades inactivos",
        estatus="B",
    )


@incapacidades.route("/incapacidades/<int:incapacidad_id>")
def detail(incapacidad_id):
    """Detalle de una Incapacidad"""
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)
    return render_template("incapacidades/detail.jinja2", incapacidad=incapacidad)


@incapacidades.route("/incapacidades/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Incapacidad"""
    form = IncapacidadForm()
    if form.validate_on_submit():
        # Validaciones
        es_valido = True
        # Validar fecha
        if form.fecha_termino.data < form.fecha_inicio.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de termino.", "warning")
            es_valido = False
        # Validar registro repetido
        registro_repetido = (
            Incapacidad.query.filter_by(persona_id=form.persona.data)
            .filter_by(fecha_inicio=form.fecha_inicio.data)
            .filter_by(fecha_termino=form.fecha_termino.data)
            .filter_by(estatus="A")
            .first()
        )
        if registro_repetido:
            flash("Esta persona ya tiene una incapacidad en la misma fecha de inicio y término.", "warning")
            es_valido = False
        # Buscar puesto en historial de puestos
        puesto_nombre = None
        historial_puesto = HistorialPuesto.query.filter_by(persona_id=form.persona.data).filter_by(estatus="A")
        historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
        historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
        if historial_puesto:
            puesto_nombre = historial_puesto.puesto_funcion.nombre
        if es_valido:
            # Guardar datos sin archivo
            if request.files["archivo"].filename == "":
                # Guardar la Licencia
                incapacidad = Incapacidad(
                    persona_id=form.persona.data,
                    fecha_inicio=form.fecha_inicio.data,
                    fecha_termino=form.fecha_termino.data,
                    clave_incapacidad=safe_string(form.clave_incapacidad.data),
                    region=form.region.data,
                    motivo=safe_string(form.motivo.data, save_enie=True),
                    puesto_nombre=puesto_nombre,
                )
                incapacidad.save()
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Nueva Incapacidad {incapacidad.persona.nombre_completo}"),
                    url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
            else:
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
                    incapacidad = Incapacidad(
                        persona_id=form.persona.data,
                        fecha_inicio=form.fecha_inicio.data,
                        fecha_termino=form.fecha_termino.data,
                        clave_incapacidad=safe_string(form.clave_incapacidad.data),
                        region=form.region.data,
                        motivo=safe_string(form.motivo.data, save_enie=True),
                        puesto_nombre=puesto_nombre,
                    )
                    incapacidad.save()
                    # Subir a Google Cloud Storage
                    es_exitoso = True
                    try:
                        storage.set_filename(hashed_id=incapacidad.encode_id(), description="INCAPACIDAD")
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
                        incapacidad.archivo = storage.filename
                        incapacidad.url = storage.url
                        incapacidad.save()
                        # Salida en bitacora
                        bitacora = Bitacora(
                            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                            usuario=current_user,
                            descripcion=safe_message(f"Nueva incapacidad {incapacidad.id}"),
                            url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
                        )
                        bitacora.save()
                        flash(bitacora.descripcion, "success")
                        return redirect(bitacora.url)
                    else:
                        return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))
    return render_template("incapacidades/new.jinja2", form=form)


@incapacidades.route("/incapacidades/nuevo_con_persona/<int:persona_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_persona_id(persona_id):
    """Nuevo Incapacidad"""
    persona = Persona.query.get_or_404(persona_id)
    form = IncapacidadWithPersonaForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        # Validaciones
        es_valido = True
        # Validar fecha
        if form.fecha_termino.data < form.fecha_inicio.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de termino.", "warning")
            es_valido = False
        # Validar registro repetido
        registro_repetido = (
            Incapacidad.query.filter_by(persona=persona)
            .filter_by(fecha_inicio=form.fecha_inicio.data)
            .filter_by(fecha_termino=form.fecha_termino.data)
            .filter_by(estatus="A")
            .first()
        )
        if registro_repetido:
            flash("Esta persona ya tiene una incapacidad en la misma fecha de inicio y término.", "warning")
            es_valido = False
        if es_valido:
            # Buscar puesto en historial de puestos
            puesto_nombre = None
            historial_puesto = HistorialPuesto.query.filter_by(persona=persona).filter_by(estatus="A")
            historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
            historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
            if historial_puesto:
                puesto_nombre = historial_puesto.puesto_funcion.nombre
            # Guardar datos sin archivo
            if request.files["archivo"].filename == "":
                # Guardar registro
                incapacidad = Incapacidad(
                    persona=persona,
                    fecha_inicio=form.fecha_inicio.data,
                    fecha_termino=form.fecha_termino.data,
                    clave_incapacidad=safe_string(form.clave_incapacidad.data),
                    region=form.region.data,
                    motivo=safe_string(form.motivo.data, save_enie=True),
                    puesto_nombre=puesto_nombre,
                )
                incapacidad.save()
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Nuevo Incapacidad {incapacidad.persona.nombre_completo}"),
                    url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
            else:
                # Guardar cambios con un archivo adjunto
                # Validar archivo
                archivo = request.files["archivo"]
                storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf", "jpg", "jpeg"])
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
                    incapacidad = Incapacidad(
                        persona=persona,
                        fecha_inicio=form.fecha_inicio.data,
                        fecha_termino=form.fecha_termino.data,
                        clave_incapacidad=safe_string(form.clave_incapacidad.data),
                        region=form.region.data,
                        motivo=safe_string(form.motivo.data, save_enie=True),
                        puesto_nombre=puesto_nombre,
                    )
                    incapacidad.save()
                    # Subir a Google Cloud Storage
                    es_exitoso = True
                    try:
                        storage.set_filename(hashed_id=incapacidad.encode_id(), description="INCAPACIDAD")
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
                        incapacidad.archivo = storage.filename
                        incapacidad.url = storage.url
                        incapacidad.save()
                        # Salida en bitacora
                        bitacora = Bitacora(
                            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                            usuario=current_user,
                            descripcion=safe_message(f"Nueva Incapacidad {incapacidad.id}"),
                            url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
                        )
                        bitacora.save()
                        flash(bitacora.descripcion, "success")
                        return redirect(bitacora.url)
                    else:
                        return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))
    form.persona.data = persona.nombre_completo
    return render_template("incapacidades/new_with_persona_id.jinja2", form=form, persona=persona)


@incapacidades.route("/incapacidades/edicion/<int:incapacidad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(incapacidad_id):
    """Editar Incapacidad"""
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)
    form = IncapacidadWithPersonaForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        # Validaciones
        es_valido = True
        # Validar fecha
        if form.fecha_termino.data < form.fecha_inicio.data:
            flash("La fecha de inicio no puede ser mayor a la fecha de termino.", "warning")
            es_valido = False
        # Validar registro repetido
        registro_repetido = (
            Incapacidad.query.filter_by(persona=incapacidad.persona)
            .filter_by(fecha_inicio=form.fecha_inicio.data)
            .filter_by(fecha_termino=form.fecha_termino.data)
            .filter_by(estatus="A")
            .filter(Incapacidad.id != incapacidad_id)
            .first()
        )
        if registro_repetido:
            flash("Esta persona ya tiene una incapacidad en la misma fecha de inicio y término.", "warning")
            es_valido = False
        if es_valido:
            # Buscar puesto en historial de puestos
            puesto_nombre = None
            historial_puesto = HistorialPuesto.query.filter_by(persona=incapacidad.persona).filter_by(estatus="A")
            historial_puesto = historial_puesto.filter(form.fecha_inicio.data >= HistorialPuesto.fecha_inicio)
            historial_puesto = historial_puesto.order_by(HistorialPuesto.fecha_inicio.desc()).first()
            if historial_puesto:
                puesto_nombre = historial_puesto.puesto_funcion.nombre
            if request.files["archivo"].filename == "":
                # Guardar cambios sin modificar el archivo
                # Guardar cambios
                incapacidad.fecha_inicio = form.fecha_inicio.data
                incapacidad.fecha_termino = form.fecha_termino.data
                incapacidad.clave_incapacidad = form.clave_incapacidad.data
                incapacidad.region = form.region.data
                incapacidad.motivo = safe_string(form.motivo.data, save_enie=True)
                incapacidad.puesto = puesto_nombre
                incapacidad.save()
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Editado Incapacidad {incapacidad.motivo}"),
                    url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
            else:
                # Guardar cambios modificando el archivo adjunto
                # Validar archivo
                archivo = request.files["archivo"]
                storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf", "jpg", "jpeg"])
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
                    incapacidad.delete()
                    # Crear nuevo registro
                    incapacidad_new = Incapacidad(
                        persona=incapacidad.persona,
                        fecha_inicio=form.fecha_inicio.data,
                        fecha_termino=form.fecha_termino.data,
                        clave_incapacidad=safe_string(form.clave_incapacidad.data),
                        region=form.region.data,
                        motivo=safe_string(form.motivo.data, save_enie=True),
                        puesto_nombre=puesto_nombre,
                    )
                    incapacidad_new.save()
                    # Subir a Google Cloud Storage
                    es_exitoso = True
                    try:
                        storage.set_filename(hashed_id=incapacidad_new.encode_id(), description="INCAPACIDAD")
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
                        incapacidad_new.archivo = storage.filename
                        incapacidad_new.url = storage.url
                        incapacidad_new.save()
                        # Salida en bitacora
                        bitacora = Bitacora(
                            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                            usuario=current_user,
                            descripcion=safe_message(
                                f"Editado Incapacidad {incapacidad_new.id}, se dio de baja {incapacidad.id}"
                            ),
                            url=url_for("incapacidades.detail", incapacidad_id=incapacidad_new.id),
                        )
                        bitacora.save()
                        flash(bitacora.descripcion, "success")
                        return redirect(bitacora.url)
                    else:
                        incapacidad_new.delete()
                        incapacidad.recover()
                        return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))
    # Cargar valores leídos
    form.persona.data = incapacidad.persona.nombre_completo
    form.fecha_inicio.data = incapacidad.fecha_inicio
    form.fecha_termino.data = incapacidad.fecha_termino
    form.clave_incapacidad.data = incapacidad.clave_incapacidad
    form.region.data = incapacidad.region
    form.motivo.data = incapacidad.motivo
    return render_template("incapacidades/edit.jinja2", form=form, incapacidad=incapacidad)


@incapacidades.route("/incapacidades/eliminar/<int:incapacidad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(incapacidad_id):
    """Eliminar Incapacidad"""
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)
    if incapacidad.estatus == "A":
        incapacidad.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Incapacidad {incapacidad.id}"),
            url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))


@incapacidades.route("/incapacidades/recuperar/<int:incapacidad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(incapacidad_id):
    """Recuperar Incapacidad"""
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)
    if incapacidad.estatus == "B":
        incapacidad.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Incapacidad {incapacidad.id}"),
            url=url_for("incapacidades.detail", incapacidad_id=incapacidad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))


@incapacidades.route("/incapacidades/<int:incapacidad_id>/pdf")
def download_pdf(incapacidad_id):
    """Descargar el archivo PDF de un Archivo"""

    # Consultar
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)

    # Si el estatus es B, no se puede descargar
    if incapacidad.estatus == "B":
        flash("No se puede descargar un archivo inactivo", "warning")
        return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))

    # Tomar el nombre del archivo con el que sera descargado
    descarga_nombre = incapacidad.archivo

    # Obtener el contenido del archivo desde Google Storage
    try:
        descarga_contenido = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(incapacidad.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        flash(str(error), "danger")
        return redirect(url_for("incapacidades.detail", incapacidad_id=incapacidad.id))

    # Descargar un archivo PDF
    response = make_response(descarga_contenido)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={descarga_nombre}"
    return response


@incapacidades.route("/incapacidades/ver_archivo_pdf/<int:incapacidad_id>")
def view_file_pdf(incapacidad_id):
    """Ver archivo PDF de Incapacidad para insertarlo en un iframe en el detalle"""

    # Consultar
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)

    # Obtener el contenido del archivo
    try:
        archivo = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(incapacidad.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        print(incapacidad.url)
        raise NotFound("No se encontró el archivo.")

    # Entregar el archivo
    response = make_response(archivo)
    response.headers["Content-Type"] = "application/pdf"
    return response


@incapacidades.route("/incapacidades/ver_archivo_img/<int:incapacidad_id>")
def view_file_img(incapacidad_id):
    """Ver archivo IMG de adjunto para insertarlo en un iframe en el detalle"""

    # Consultar
    incapacidad = Incapacidad.query.get_or_404(incapacidad_id)

    # Obtener el contenido del archivo
    try:
        archivo = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO"],
            blob_name=get_blob_name_from_url(incapacidad.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        print(incapacidad.url)
        raise NotFound("No se encontró el archivo.")

    # Entregar el archivo
    response = make_response(archivo)
    response.headers["Content-Type"] = "image/jpeg"
    return response
