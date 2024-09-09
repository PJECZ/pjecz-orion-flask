"""
Personas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Optional

from orion.blueprints.carreras.models import Carrera
from orion.blueprints.niveles_academicos.models import NivelAcademico
from orion.blueprints.personas.models import Persona


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


class PersonaEditDatosAcademicosForm(FlaskForm):
    """Editar el Domicilio Fiscal de una Persona"""

    persona = StringField("Persona")  # ReadOnly
    nivel_estudios = SelectField("Tipo", choices=Persona.ESTUDIOS.items(), validators=[DataRequired()])
    nivel_max_estudios = SelectField("Nivel Máximo de Estudios", coerce=int, validators=[DataRequired()])
    carrera = SelectField("Carrera", coerce=int, validators=[DataRequired()])
    cedula_profesional = StringField("Cédula Profesional", validators=[Optional(), Length(max=16)])
    guardar = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        """Inicializar y cargar opciones de nivel_max_estudios"""
        super().__init__(*args, **kwargs)
        # Nivel Máximo de Estudios
        self.nivel_max_estudios.choices = [
            (r.id, f"{r.clave}: {r.nombre}")
            for r in NivelAcademico.query.filter_by(estatus="A").order_by(NivelAcademico.nombre).all()
        ]
        # Carreras
        self.carrera.choices = [
            (r.id, f"{r.nombre}") for r in Carrera.query.filter_by(estatus="A").order_by(Carrera.nombre).all()
        ]
