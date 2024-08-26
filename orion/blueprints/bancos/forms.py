"""
Bancos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class BancoForm(FlaskForm):
    """Formulario Banco"""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=64)])
    guardar = SubmitField("Guardar")
