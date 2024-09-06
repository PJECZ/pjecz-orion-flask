"""
Personas Nombramientos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, FileField
from wtforms.validators import DataRequired, Length, Optional


class PersonaNombramientoForm(FlaskForm):
    """Formulario PersonaNombramiento"""

    persona = StringField("Persona")  # ReadOnly
    cargo = StringField("Cargo", validators=[DataRequired(), Length(max=64)])
    centro_trabajo = StringField("Centro de Trabajo", validators=[DataRequired(), Length(max=128)])
    tipo = StringField("Tipo de Nombramiento", validators=[Optional(), Length(max=64)])
    fecha_inicio = DateField("Fecha Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha Término", validators=[Optional()])
    archivo = FileField("Archivo Adjunto o Imagen", validators=[Optional()])
    guardar = SubmitField("Guardar")
