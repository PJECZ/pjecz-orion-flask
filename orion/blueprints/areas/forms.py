"""
Área, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional


class AreaForm(FlaskForm):
    """Formulario Area"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=128)])
    centro_trabajo = SelectField("Centro de Trabajo", coerce=int, validate_choice=False, validators=[DataRequired()])
    guardar = SubmitField("Guardar")
