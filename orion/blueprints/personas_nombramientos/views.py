"""
Personas Nombramientos, vistas
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
from orion.blueprints.personas_nombramientos.models import PersonaNombramiento
from orion.blueprints.personas_nombramientos.forms import PersonaNombramientoForm

from lib.exceptions import (
    MyAnyError,
    MyFilenameError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyUnknownExtensionError,
)
from lib.storage import GoogleCloudStorage


MODULO = "PERSONAS NOMBRAMIENTOS"

personas_nombramientos = Blueprint("personas_nombramientos", __name__, template_folder="templates")

SUBDIRECTORIO = "nombramientos"


@personas_nombramientos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@personas_nombramientos.route("/personas_nombramientos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Nombramientos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PersonaNombramiento.query
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
    registros = consulta.order_by(PersonaNombramiento.fecha_inicio.desc()).offset(start).limit(rows_per_page).all()
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
                    "url": url_for("personas_nombramientos.detail", persona_nombramiento_id=resultado.id),
                },
                "cargo": resultado.cargo,
                "centro_trabajo": resultado.centro_trabajo,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@personas_nombramientos.route("/personas_nombramientos/<int:persona_nombramiento_id>")
def detail(persona_nombramiento_id):
    """Detalle de un Nombramiento"""
    persona_nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    return render_template("personas_nombramientos/detail.jinja2", persona_nombramiento=persona_nombramiento)


# TODO: NEW_WITH_PERSONA_ID


@personas_nombramientos.route("/personas_nombramientos/edicion/<int:persona_nombramiento_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(persona_nombramiento_id):
    """Editar Nombramiento"""
    nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    form = PersonaNombramientoForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        es_valido = True
        # Validar fecha
        if form.fecha_inicio.data > form.fecha_termino.data:
            flash(f"La fecha de inicio no puede ser mayor a la fecha de término.", "warning")
            es_valido = False
        if es_valido:
            if request.files["archivo"].filename == "":
                # Guardar cambios sin modificar el archivo
                nombramiento.cargo = safe_string(form.cargo.data)
                nombramiento.centro_trabajo = safe_string(form.centro_trabajo.data)
                nombramiento.tipo = safe_string(form.tipo.data)
                nombramiento.fecha_inicio = form.fecha_inicio.data
                nombramiento.fecha_termino = form.fecha_termino.data
                nombramiento.save()
                # Salida en bitacora
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Editado Nombramiento {nombramiento.id}"),
                    url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
            else:
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
                    nombramiento.delete()
                    nombramiento_new = PersonaNombramiento(
                        persona=nombramiento.persona,
                        cargo=safe_string(form.cargo.data),
                        centro_trabajo=safe_string(form.centro_trabajo.data),
                        tipo=safe_string(form.tipo.data),
                        fecha_inicio=form.fecha_inicio.data,
                        fecha_termino=form.fecha_termino.data,
                    )
                    nombramiento_new.save()
                    # Subir a Google Cloud Storage
                    es_exitoso = True
                    try:
                        storage.set_filename(hashed_id=nombramiento_new.encode_id(), description="NOMBRAMIENTO")
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
                        nombramiento_new.archivo = storage.filename
                        nombramiento_new.url = storage.url
                        nombramiento_new.save()
                        # Salida en bitacora
                        bitacora = Bitacora(
                            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                            usuario=current_user,
                            descripcion=safe_message(
                                f"Editado Nombramiento {nombramiento_new.id}, se dio de baja {nombramiento.id}"
                            ),
                            url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento_new.id),
                        )
                        bitacora.save()
                        flash(bitacora.descripcion, "success")
                        return redirect(bitacora.url)
                    else:
                        nombramiento_new.delete()
                        nombramiento.recover()
                        return redirect(url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id))
    form.persona.data = nombramiento.persona.nombre_completo
    form.cargo.data = nombramiento.cargo
    form.centro_trabajo.data = nombramiento.centro_trabajo
    form.tipo.data = nombramiento.tipo
    form.fecha_inicio.data = nombramiento.fecha_inicio
    form.fecha_termino.data = nombramiento.fecha_termino
    return render_template("personas_nombramientos/edit.jinja2", form=form, persona_nombramiento=nombramiento)


@personas_nombramientos.route("/personas_nombramientos/eliminar/<int:persona_nombramiento_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(persona_nombramiento_id):
    """Eliminar Nombramiento"""
    nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    if nombramiento.estatus == "A":
        nombramiento.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Nombramiento {nombramiento.id}"),
            url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id))


@personas_nombramientos.route("/personas_nombramientos/recuperar/<int:persona_nombramiento_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(persona_nombramiento_id):
    """Recuperar Nombramiento"""
    nombramiento = PersonaNombramiento.query.get_or_404(persona_nombramiento_id)
    if nombramiento.estatus == "B":
        nombramiento.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Nombramiento {nombramiento.id}"),
            url=url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("personas_nombramientos.detail", persona_nombramiento_id=nombramiento.id))
