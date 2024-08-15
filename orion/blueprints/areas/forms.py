"""
Área, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class AreaForm(FlaskForm):
    """Formulario Area"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=128)])
    centro_trabajo = StringField("Centro de Trabajo", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
