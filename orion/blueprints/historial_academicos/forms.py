"""
Historial Académicos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Optional
from orion.blueprints.niveles_academicos.models import NivelAcademico


class HistorialAcademicoForm(FlaskForm):
    """Formulario HistorialAcademico"""

    persona = SelectField("Persona", coerce=int, validate_choice=False, validators=[DataRequired()])
    nivel_academico = SelectField("Nivel Académico", coerce=int, validators=[DataRequired()])
    nombre_escuela = StringField("Escuela", validators=[Optional(), Length(max=64)])
    nombre_ciudad = StringField("Ciudad, Estado", validators=[Optional(), Length(max=64)])
    ano_inicio = IntegerField("Año de Inicio", validators=[Optional()])
    ano_termino = IntegerField("Año de Término", validators=[Optional()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de niveles_academicos"""
        super().__init__(*args, **kwargs)
        self.nivel_academico.choices = [
            (r.id, f"{r.clave}: {r.nombre}")
            for r in NivelAcademico.query.filter_by(estatus="A").order_by(NivelAcademico.nombre).all()
        ]


class HistorialAcademicoWithPersonaForm(FlaskForm):
    """Formulario HistorialAcademico"""

    persona = StringField("Persona")  # ReadOnly
    nivel_academico = SelectField("Nivel Académico", coerce=int, validators=[DataRequired()])
    nombre_escuela = StringField("Escuela", validators=[Optional(), Length(max=64)])
    nombre_ciudad = StringField("Ciudad, Estado", validators=[Optional(), Length(max=64)])
    ano_inicio = IntegerField("Año de Inicio", validators=[Optional()])
    ano_termino = IntegerField("Año de Término", validators=[Optional()])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de niveles_academicos"""
        super().__init__(*args, **kwargs)
        self.nivel_academico.choices = [
            (r.id, f"{r.clave}: {r.nombre}")
            for r in NivelAcademico.query.filter_by(estatus="A").order_by(NivelAcademico.nombre).all()
        ]
