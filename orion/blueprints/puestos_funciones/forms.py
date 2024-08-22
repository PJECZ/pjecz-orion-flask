"""
Puestos Funciones, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class PuestoFuncionForm(FlaskForm):
    """Formulario PuestoFuncion"""

    puesto = StringField("Puesto")  # ReadOnly
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=128)])
    guardar = SubmitField("Guardar")
