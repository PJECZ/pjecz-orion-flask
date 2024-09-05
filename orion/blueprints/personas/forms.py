"""
Personas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional


class PersonaForm(FlaskForm):
    """Formulario Persona"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=16)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")


class PersonaEditDomicilioFiscalForm(FlaskForm):
    """Editar el Domicilio Fiscal de una Persona"""

    persona = StringField("Persona")  # ReadOnly
    calle = StringField("Calle", validators=[DataRequired(), Length(max=128)])
    numero_exterior = StringField("Número Exterior", validators=[DataRequired(), Length(max=16)])
    numero_interior = StringField("Número Interior", validators=[Optional(), Length(max=16)])
    colonia = StringField("Colonia", validators=[DataRequired(), Length(max=64)])
    localidad = StringField("Localidad", validators=[DataRequired(), Length(max=64)])
    municipio = StringField("Municipio", validators=[DataRequired(), Length(max=64)])
    estado = StringField("Estado", validators=[DataRequired(), Length(max=64)])
    codigo_postal = IntegerField("Código Postal", validators=[DataRequired()])
    guardar = SubmitField("Guardar")
