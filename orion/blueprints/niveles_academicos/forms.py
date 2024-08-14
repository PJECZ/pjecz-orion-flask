"""
Niveles Académicos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class NivelAcademicoForm(FlaskForm):
    """Formulario NivelAcademico"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=8)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=64)])
    guardar = SubmitField("Guardar")
