"""
Carreras, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class CarreraForm(FlaskForm):
    """Formulario Carrera"""

    nombre = StringField("Descripción", validators=[DataRequired(), Length(max=128)])
    guardar = SubmitField("Guardar")
