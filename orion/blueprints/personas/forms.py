"""
Personas, formularios
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DateField, BooleanField, RadioField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Email

from orion.blueprints.carreras.models import Carrera
from orion.blueprints.niveles_academicos.models import NivelAcademico
from orion.blueprints.personas.models import Persona


class PersonaForm(FlaskForm):
    """Formulario Persona"""

    nombres = StringField("Nombres", validators=[DataRequired(), Length(max=128)])
    apellido_primero = StringField("Apellido Primero", validators=[DataRequired(), Length(max=128)])
    apellido_segundo = StringField("Apellido Segundo", validators=[Optional(), Length(max=128)])
    sexo = SelectField("Sexo", choices=Persona.SEXOS.items(), validators=[DataRequired()])
    curp = StringField("CURP", validators=[DataRequired()])
    rfc = StringField("RFC", validators=[DataRequired()])
    email = StringField("e-mail", validators=[Email()])
    telefono_trabajo = StringField("Teléfono del Trabajo", validators=[Length(max=64)])
    telefono_trabajo_extension = StringField("Teléfono del Trabajo Extensión", validators=[Length(max=16)])
    situacion = SelectField("Situación", choices=Persona.SITUACIONES.items(), validators=[Optional()])
    fecha_baja = DateField("Fecha de Baja", validators=[Optional()])
    numero_empleado_opciones = RadioField(
        "Opciones para el Número de Empelado", choices=Persona.ESTADOS.items(), validators=[Optional()]
    )
    numero_empleado = IntegerField("Número de Empleado", validators=[Optional()])
    falta_papeleria = BooleanField("Le falta papelería")
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
    """Editar el Datos Académicos de una Persona"""

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


class PersonaEditDatosPersonalesForm(FlaskForm):
    """Editar los Datos Personales de una Persona"""

    persona = StringField("Persona")  # ReadOnly
    fecha_ingreso_gob = DateField("Fecha de ingreso en Gobierno del Estado")
    fecha_ingreso_pj = DateField("Fecha de ingreso al Poder Judicial")
    num_seguridad_social = StringField("Número de Seguridad Social")
    estado_civil = SelectField("Estado Civil", choices=Persona.ESTADOS_CIVILES.items(), validators=[DataRequired()])
    fecha_nacimiento = DateField("Fecha de Nacimiento")
    telefono_personal = StringField("Teléfono Personal")
    telefono_domicilio = StringField("Teléfono Domicilio")
    email_secundario = StringField("Email Personal", validators=[Email()])
    es_madre = BooleanField("¿Es Madre?")
    guardar = SubmitField("Guardar")


class PersonaEditDatosGeneralesForm(FlaskForm):
    """Editar los Datos Generales de una Persona"""

    persona = StringField("Persona")  # ReadOnly
    nombres = StringField("Nombres", validators=[DataRequired(), Length(max=128)])
    apellido_primero = StringField("Apellido Primero", validators=[DataRequired(), Length(max=128)])
    apellido_segundo = StringField("Apellido Segundo", validators=[Optional(), Length(max=128)])
    sexo = SelectField("Sexo", choices=Persona.SEXOS.items(), validators=[DataRequired()])
    curp = StringField("CURP")
    rfc = StringField("RFC")
    email = StringField("e-mail", validators=[Email()])
    telefono_trabajo = StringField("Teléfono del Trabajo", validators=[Length(max=64)])
    telefono_trabajo_extension = StringField("Teléfono del Trabajo Extensión", validators=[Length(max=16)])
    situacion = SelectField("Situación", choices=Persona.SITUACIONES.items(), validators=[Optional()])
    fecha_baja = DateField("Fecha de Baja", validators=[Optional()])
    numero_empleado_opciones = RadioField("Opciones para el Número de Empelado", choices=Persona.ESTADOS.items())
    numero_empleado = IntegerField("Número de Empleado", validators=[Optional()])
    falta_papeleria = BooleanField("Le falta papelería")
    guardar = SubmitField("Guardar")


class PersonaEditObservacionesForm(FlaskForm):
    """Editar los Observaciones de una Persona"""

    persona = StringField("Persona")  # ReadOnly
    observaciones = TextAreaField("Observaciones", validators=[Length(max=512)])
    observaciones_especiales = TextAreaField("Observaciones Especiales", validators=[Length(max=512)])
    guardar = SubmitField("Guardar")
