"""
Personas Actas Administrativas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, Optional


class PersonaActaAdministrativaForm(FlaskForm):
    """Formulario PersonaActaAdministrativa"""

    persona = StringField("Persona")  # ReadOnly
    fecha = DateField("Fecha", validators=[DataRequired()])
    falta = StringField("Falta", validators=[Optional()])
    sancion = StringField("Sanción", validators=[Optional()])
    guardar = SubmitField("Guardar")
