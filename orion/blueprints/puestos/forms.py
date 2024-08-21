"""
Puestos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.puestos.models import Puesto


class PuestoForm(FlaskForm):
    """Formulario Puesto"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=32)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=128)])
    tipo_cargo = SelectField("Tipo de Cargo", choices=Puesto.CARGOS.items(), validators=[DataRequired()])
    tipo_empleado = SelectField("Tipo de Empleados", choices=Puesto.TIPOS_EMPLEADOS.items(), validators=[DataRequired()])
    guardar = SubmitField("Guardar")
