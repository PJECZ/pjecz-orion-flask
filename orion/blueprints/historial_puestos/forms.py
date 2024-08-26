"""
Historial de Puestos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class HistorialPuestoForm(FlaskForm):
    """Formulario HistorialPuesto"""

    persona = StringField("Persona")  # readonly
    puesto = SelectField(label="Puesto", coerce=int, validate_choice=False)
    funcion = SelectField(label="Funcion", coerce=int, validate_choice=False, validators=[DataRequired()])
    centro_trabajo = SelectField(label="Centros de Trabajo", coerce=int, validate_choice=False, validators=[DataRequired()])
    area = SelectField(label="Área", coerce=int, validate_choice=False, validators=[DataRequired()])
    turno = SelectField(label="Turno", coerce=int, validate_choice=False, validators=[DataRequired()])
    fecha_inicio = DateField("Fecha de Inicio", validators=[DataRequired()])
    fecha_termino = DateField("Fecha de Termino", validators=[Optional()])
    nivel = IntegerField("Nivel", validators=[DataRequired(), NumberRange(min=1, max=7)])
    quinquenio = IntegerField("Quinquenio", validators=[Optional(), NumberRange(min=0, max=6)])
    nombramiento = StringField("Nombramiento", validators=[Optional(), Length(max=128)])
    tipo_nombramiento = StringField("Tipo Nombramiento", validators=[Optional(), Length(max=128)])
    nombramiento_observaciones = StringField("Nombramiento Observaciones", validators=[Optional(), Length(max=128)])
    guardar = SubmitField("Guardar")
