"""
Personas Actas Protestas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, DateField
from wtforms.validators import DataRequired, Length, Optional


class PersonasActasProtestasForm(FlaskForm):
    """Formulario PersonasActasProtestas"""

    persona = StringField("Persona")  # ReadOnly
    fecha = DateField("Fecha", validators=[Optional()])
    cargo = StringField("Cargo", validators=[Optional(), Length(max=256)])
    archivo = FileField("Archivo Adjunto", validators=[Optional()])
    guardar = SubmitField("Guardar")
