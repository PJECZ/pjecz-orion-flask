"""
Turnos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class TurnoForm(FlaskForm):
    """Formulario Turno"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=64)])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=64)])
    guardar = SubmitField("Guardar")
