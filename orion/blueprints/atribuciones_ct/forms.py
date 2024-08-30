"""
Atribuciones CT, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length


class AtribucionCTForm(FlaskForm):
    """Formulario AtribucionCT"""

    centro_trabajo = SelectField("Centro de Trabajo", coerce=int, validate_choice=False, validators=[DataRequired()])
    area = SelectField("Área", coerce=int, validate_choice=False, validators=[DataRequired()])
    norma = StringField("Norma", validators=[DataRequired(), Length(max=512)])
    fundamento = StringField("Fundamento", validators=[DataRequired(), Length(max=512)])
    fragmento = StringField("Fragmento", validators=[DataRequired(), Length(max=512)])
    guardar = SubmitField("Guardar")
