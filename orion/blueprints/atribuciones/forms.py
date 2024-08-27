"""
Atribuciones, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.atribuciones.models import Atribucion


class AtribucionForm(FlaskForm):
    """Formulario Atribucion"""

    centro_trabajo = SelectField(label="Centros de Trabajo", coerce=int, validate_choice=False, validators=[DataRequired()])
    puesto = SelectField(label="Puesto", coerce=int, validate_choice=False)
    funcion = SelectField(label="Funcion", coerce=int, validate_choice=False, validators=[DataRequired()])
    tipo_cargo = SelectField("Tipo de Cargo", choices=Atribucion.CARGOS.items(), validators=[DataRequired()])
    norma = StringField("Norma", validators=[Length(max=512)])
    fundamento = StringField("Fundamento", validators=[Length(max=512)])
    fragmento = StringField("Fragmento", validators=[Length(max=512)])
    guardar = SubmitField("Guardar")
