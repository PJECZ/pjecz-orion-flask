"""
Licencias, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.licencias.models import Licencia


class LicenciaForm(FlaskForm):
    """Formulario Licencia"""

    persona = SelectField("Persona", coerce=int, validate_choice=False, validators=[DataRequired()])
    tipo = SelectField("Tipo", choices=Licencia.TIPOS.items(), validators=[DataRequired()])
    fecha_inicio = DateField("Fecha de Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha de Termino", validators=[DataRequired()])
    con_goce = RadioField(
        "Con Goce de Sueldo",
        choices=[("True", "Con Goce"), ("False", "Sin Goce")],
        coerce=lambda value: value == "True",
    )
    dias = IntegerField("Días")
    motivo = StringField("Motivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class LicenciaWithPersonaForm(FlaskForm):
    """Formulario Licencia"""

    persona = StringField("Persona")
    tipo = SelectField("Tipo", choices=Licencia.TIPOS.items(), validators=[DataRequired()])
    fecha_inicio = DateField("Fecha de Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha de Termino", validators=[DataRequired()])
    con_goce = RadioField(
        "Con Goce de Sueldo",
        choices=[("True", "Con Goce"), ("False", "Sin Goce")],
        coerce=lambda value: value == "True",
    )
    dias = IntegerField("Días")
    motivo = StringField("Motivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
