"""
Centros de Trabajos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, Optional


class CentroTrabajoForm(FlaskForm):
    """Formulario CentroTrabajo"""

    clave = StringField("Clave", validators=[DataRequired(), Length(max=16)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=128)])
    distrito = SelectField("Distrito", coerce=int, validate_choice=False, validators=[DataRequired()])
    organo = SelectField("Órgano", coerce=int, validate_choice=False, validators=[DataRequired()])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=128)])
    num_ext = StringField("Núm. de Ext.", validators=[Optional(), Length(max=64)])
    activo = RadioField(
        "Activo",
        choices=[("True", "Activo"), ("False", "Inactivo")],
        coerce=lambda value: value == "True",
    )
    guardar = SubmitField("Guardar")
