"""
Incapacidades, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.incapacidades.models import Incapacidad


class IncapacidadForm(FlaskForm):
    """Formulario Incapacidad"""

    persona = SelectField("Persona", coerce=int, validate_choice=False, validators=[DataRequired()])
    fecha_inicio = DateField("Fecha de Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha de Termino", validators=[DataRequired()])
    dias = IntegerField("Días")
    clave_incapacidad = StringField("Clave Incapacidad", validators=[DataRequired()])
    region = SelectField("Región", choices=Incapacidad.REGIONES.items(), validators=[DataRequired()])
    motivo = StringField("Motivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class IncapacidadWithPersonaForm(FlaskForm):
    """Formulario Incapacidad"""

    persona = StringField("Persona")  # ReadOnly
    fecha_inicio = DateField("Fecha de Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha de Termino", validators=[DataRequired()])
    dias = IntegerField("Días")
    clave_incapacidad = StringField("Clave Incapacidad", validators=[DataRequired()])
    region = SelectField("Región", choices=Incapacidad.REGIONES.items(), validators=[DataRequired()])
    motivo = StringField("Motivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
