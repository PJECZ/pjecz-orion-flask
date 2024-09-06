"""
Personas, modelos
"""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Persona(database.Model, UniversalMixin):
    """Persona"""

    ESTADOS = {
        "TEMP": "Asimilados",  # Número Temporal y Automático
        "MANUAL": "Nómina Regular",  # Ingreso Manual del número
    }

    SEXOS = {
        "H": "Hombre",
        "M": "Mujer",
    }

    ESTADOS_CIVILES = {
        "C": "C: Casado",
        "D": "D: Divorciado",
        "S": "S: Soltero",
        "UL": "UL: Unión Libre",
        "V": "V: Viudo",
    }

    SITUACIONES = {
        "A.D.": "A.D: Alta Definitiva",
        "A.I.": "A.I: Alta Interina",
        "A.D.(B)": "A.D.(B): Alta Definitiva con Beneficiarios",
        "A.D.C.S.": "A.D.C.S: Alta Definitiva Comisionada al Sindicato",
        "A.D.SUS": "A.D.SUS: Alta Definitiva Suspendida",
        "A.S.": "A.S. Asimilado",
        "B": "B: Baja",
        "C.E.": "C.E: Comisión Especial",
        "L.G.": "L.G: Licencia por Gravidez",
        "L.S.G.S.": "L.S.G.S: Licencia Sin Goce de Sueldo",
        "L.P.O.P.C.": "L.P.O.P.C: Licencia Para Ocupar Puesto de Confianza",
        "V": "V: Vacante",
        "P": "P: Pensionado",
    }

    ESTUDIOS = {
        "00": "00: Sin Estudios",
        "A0": "A0: Primaria",
        "B0": "B0: Carrera Comercial",
        "C0": "C0: Carrera Técnica",
        "D0": "D0: Secundaria",
        "E0": "E0: Bachillerato",
        "F0": "F0: Normal",
        "G0": "G0: Normal Superior",
        "H0": "H0: Pasante Carrera Profesional",
        "I0": "I0: Profesional",
        "J0": "J0: Postgrado",
        "K0": "K0: Maestría",
        "L0": "L0: Diplomado/Especialidad",
        "Z0": "Z0: Licenciatura",
        "Z1": "Z1: Técnico",
        "Z3": "Z3: Doctorado",
    }

    # Nombre de la tabla
    __tablename__ = "personas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    # ciudad_nacimiento_id = db.Column(db.Integer, db.ForeignKey("cat_ciudades.id"))
    # ciudad_nacimiento = db.relationship("CatCiudad", back_populates="personas")
    carrera_id: Mapped[int] = mapped_column(ForeignKey("carreras.id"))
    carrera: Mapped["Carrera"] = relationship(back_populates="personas")
    nivel_estudios_max_id: Mapped[int] = mapped_column(ForeignKey("niveles_academicos.id"))
    nivel_estudios_max: Mapped["NivelAcademico"] = relationship(back_populates="personas")

    # Columnas
    nombres: Mapped[str] = mapped_column(String(128))
    apellido_primero: Mapped[str] = mapped_column(String(128))
    apellido_segundo: Mapped[Optional[str]] = mapped_column(String(128))
    numero_empleado: Mapped[Optional[int]] = mapped_column(unique=True)
    numero_empleado_temporal: Mapped[bool] = mapped_column(default=False)
    rfc: Mapped[str] = mapped_column(String(13))
    curp: Mapped[str] = mapped_column(String(18), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(64))
    email_secundario: Mapped[Optional[str]] = mapped_column(String(64))
    telefono_personal: Mapped[Optional[str]] = mapped_column(String(32))
    telefono_domicilio: Mapped[Optional[str]] = mapped_column(String(16))
    telefono_trabajo: Mapped[Optional[str]] = mapped_column(String(64))
    telefono_trabajo_extension: Mapped[Optional[str]] = mapped_column(String(16))
    fecha_ingreso_gobierno: Mapped[date]
    fecha_ingreso_pj: Mapped[date]
    fecha_nacimiento: Mapped[date]
    num_seguridad_social: Mapped[Optional[str]] = mapped_column(String(16))
    situacion: Mapped[str] = mapped_column(Enum(*SITUACIONES, name="personas_situaciones", native_enum=False), index=True)
    sexo: Mapped[str] = mapped_column(Enum(*SEXOS, name="personas_sexos", native_enum=False), index=True)
    estado_civil: Mapped[str] = mapped_column(
        Enum(*ESTADOS_CIVILES, name="personas_estados_civiles", native_enum=False), index=True
    )
    madre: Mapped[bool] = mapped_column(default=False)  # TODO: Cambiar a es_madre
    nivel_estudios: Mapped[Optional[str]] = mapped_column(
        Enum(*ESTUDIOS, name="personas_nivel_estudios", native_enum=False), index=False
    )
    cedula_profesional: Mapped[Optional[str]] = mapped_column(String(16))
    observaciones: Mapped[Optional[str]] = mapped_column(String(512))
    observaciones_especiales: Mapped[Optional[str]] = mapped_column(String(512))

    # Domicilio Fiscal
    domicilio_fiscal_calle: Mapped[Optional[str]] = mapped_column(String(128))
    domicilio_fiscal_numero_exterior: Mapped[Optional[str]] = mapped_column(String(16))
    domicilio_fiscal_numero_interior: Mapped[Optional[str]] = mapped_column(String(16))
    domicilio_fiscal_colonia: Mapped[Optional[str]] = mapped_column(String(64))
    domicilio_fiscal_localidad: Mapped[Optional[str]] = mapped_column(String(64))
    domicilio_fiscal_municipio: Mapped[Optional[str]] = mapped_column(String(64))
    domicilio_fiscal_estado: Mapped[Optional[str]] = mapped_column(String(64))
    domicilio_fiscal_cp: Mapped[Optional[int]]

    # Datos Extra
    fecha_baja: Mapped[Optional[date]]
    falta_papeleria: Mapped[Optional[bool]] = mapped_column(default=False)

    # Hijos
    # TODO: Conectar hijos
    # fotografias = db.relationship("PersonaFotografia", back_populates="persona")
    # sistemas = db.relationship("SistemaPersona", back_populates="persona")
    # cursos = db.relationship("PersonaCurso", back_populates="persona")
    # familiares = db.relationship("PersonaFamiliar", back_populates="persona")
    # personas_domicilios = db.relationship("PersonaDomicilio", back_populates="persona")
    personas_domicilios: Mapped[List["PersonaDomicilio"]] = relationship(back_populates="persona")
    # personas_enfermedades = db.relationship("PersonaEnfermedad", back_populates="persona")
    historial_puestos: Mapped[List["HistorialPuesto"]] = relationship(back_populates="persona")
    historial_academicos: Mapped[List["HistorialAcademico"]] = relationship(back_populates="persona")
    # historial_academicos = db.relationship("HistorialAcademico", back_populates="persona")
    # historial_laborales = db.relationship("HistorialLaboral", back_populates="persona")
    licencias: Mapped[List["Licencia"]] = relationship(back_populates="persona")
    incapacidades: Mapped[List["Incapacidad"]] = relationship(back_populates="persona")
    # parentescos = db.relationship("PersonaFamiliarPJ", foreign_keys="PersonaFamiliarPJ.persona_id")
    # parientes = db.relationship("PersonaFamiliarPJ", foreign_keys="PersonaFamiliarPJ.pariente_id")
    # pensiones_alimenticias = db.relationship("PersonaPensionAlimenticia", back_populates="persona")
    # personas_meritos = db.relationship("PersonaMerito", back_populates="persona")
    # personas_actas_administrativas = db.relationship("PersonaActaAdministrativa", back_populates="persona")
    # personas_procedimientos_diciplinarios = db.relationship("PersonaProcedimientoDiciplinario", back_populates="persona")
    # personas_escalafones = db.relationship("PersonaEscalafon", back_populates="persona")
    adjuntos: Mapped[List["PersonaAdjunto"]] = relationship(back_populates="persona")
    nombramientos: Mapped[List["PersonaNombramiento"]] = relationship(back_populates="persona")

    @property
    def nombre_completo(self):
        """Junta nombres, apellido primero y apellido segundo"""
        return self.nombres + " " + self.apellido_primero + " " + self.apellido_segundo

    def __repr__(self):
        """Representación"""
        return f"<Persona {self.id}>"
