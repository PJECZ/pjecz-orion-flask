"""
Domicilios, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional


class DomicilioForm(FlaskForm):
    """Formulario Domicilio"""

    persona = StringField("Persona")  # ReadOnly
    calle = StringField("Calle", validators=[DataRequired(), Length(max=128)])
    numero_exterior = StringField("Número Exterior", validators=[DataRequired(), Length(max=16)])
    numero_interior = StringField("Número Interior", validators=[Optional(), Length(max=16)])
    colonia = StringField("Colonia", validators=[DataRequired(), Length(max=64)])
    municipio = StringField("Municipio", validators=[DataRequired(), Length(max=64)])
    estado = StringField("Estado", validators=[DataRequired(), Length(max=64)])
    pais = StringField("País", validators=[DataRequired(), Length(max=64)])
    codigo_postal = StringField("Código Postal", validators=[Optional()])
    guardar = SubmitField("Guardar")
