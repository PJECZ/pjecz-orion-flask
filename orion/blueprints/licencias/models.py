"""
Licencias, modelos
"""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Licencia(database.Model, UniversalMixin):
    """Licencia"""

    TIPOS = {
        "SIN ESPECIFICAR": "Sin especificar",
        "ENFERMEDAD": "Enfermedad",
        "PERMISO": "Permiso",
        "VACACIONES": "Vacaciones",
        "OTRO": "Otro",
    }

    # Nombre de la tabla
    __tablename__ = "licencias"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="licencias")

    # Columnas
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS, name="licencias_tipos", native_enum=False), index=True)
    fecha_inicio: Mapped[date]
    fecha_termino: Mapped[date]
    con_goce: Mapped[bool] = mapped_column(default=False)
    motivo: Mapped[str] = mapped_column(String(512))
    puesto_nombre: Mapped[str] = mapped_column(String(128))

    def __repr__(self):
        """Representación"""
        return f"<Licencia {self.id}>"
