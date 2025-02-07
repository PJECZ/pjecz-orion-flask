"""
Municipios, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class MunicipioForm(FlaskForm):
    """Formulario Municipio"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=3)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
