"""
Persona Actas Administrativas, vistas
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
from orion.blueprints.personas_actas_administrativas.models import PersonaActaAdministrativa

MODULO = "PERSONAS ACTAS ADMINISTRATIVAS"

personas_actas_administrativas = Blueprint("personas_actas_administrativas", __name__, template_folder="templates")


@personas_actas_administrativas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""
