"""
Personas Fotografías, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, Optional


class PersonaFotografiaForm(FlaskForm):
    """Formulario PersonaFotografia"""

    persona = StringField("Persona")  # ReadOnly
    archivo = FileField("Archivo", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
