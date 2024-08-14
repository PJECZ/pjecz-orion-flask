"""
Personas, modelos
"""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid, Date
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

    # Columnas
    nombres: Mapped[str] = mapped_column(String(16), unique=True)
    apellido_primero: Mapped[str] = mapped_column(String(128))
    apellido_segundo: Mapped[Optional[str]] = mapped_column(String(128))
    numero_empleado: Mapped[int] = mapped_column(unique=True)
    numero_empleado_temporal: Mapped[bool] = mapped_column(default=False)
    rfc: Mapped[str] = mapped_column(String(13))
    curp: Mapped[str] = mapped_column(String(18), unique=True)
    email: Mapped[str] = mapped_column(String(64))
    email_secundario: Mapped[str] = mapped_column(String(64))
    telefono_personal: Mapped[str] = mapped_column(String(32))
    telefono_domicilio: Mapped[str] = mapped_column(String(16))
    telefono_trabajo: Mapped[str] = mapped_column(String(64))
    telefono_trabajo_extension: Mapped[str] = mapped_column(String(16))
    fecha_ingreso_gobierno: Mapped[date]
    fecha_ingreso_pj: Mapped[date]
    fecha_nacimiento: Mapped[date]
    num_seguridad_social: Mapped[str] = mapped_column(String(16))
    situacion = Mapped[str] = mapped_column(Enum(*SITUACIONES, name="personas_situaciones", native_enum=False), index=True)
    sexo = Mapped[str] = mapped_column(Enum(*SEXOS, name="personas_sexos", native_enum=False), index=True)
    estado_civil = Mapped[str] = mapped_column(
        Enum(*ESTADOS_CIVILES, name="personas_estados_civiles", native_enum=False), index=True
    )
    es_madre: Mapped[bool] = mapped_column(default=False)
    # nivel_estudios:
    # cedula_profesional:
    # observaciones:
    # observaciones_especiales:
    # # Domicilio Fiscal
    # # Datos Extra
    # fecha_baja:
    falta_papeleria: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        """Representación"""
        return f"<Persona {self.id}>"
