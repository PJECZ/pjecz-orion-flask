"""
Personas Archivos Adjuntos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.personas_adjuntos.models import PersonaAdjunto


class PersonaAdjuntoForm(FlaskForm):
    """Formulario PersonaAdjunto"""

    persona = StringField("Persona")  # ReadOnly
    tipo = SelectField("Tipo de Archivo", choices=PersonaAdjunto.TIPOS.items(), validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=128)])
    archivo = FileField("Archivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class PersonaAdjuntoEditForm(FlaskForm):
    """Formulario PersonaAdjunto"""

    persona = StringField("Persona")  # ReadOnly
    tipo = SelectField("Tipo de Archivo", choices=PersonaAdjunto.TIPOS.items(), validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=128)])
    archivo = FileField("Archivo", validators=[Optional()])
    guardar = SubmitField("Guardar")
