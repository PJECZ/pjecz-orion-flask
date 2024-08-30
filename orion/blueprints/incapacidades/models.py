"""
Incapacidades, modelos
"""

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Incapacidad(database.Model, UniversalMixin):
    """Incapacidad"""

    REGIONES = {
        "SIN DEFINIR": "Sin Definir",
        "CARBONIFERA": "Carbonífera",
        "SURESTE": "Sureste",
        "CENTRO": "Centro",
        "NORTE": "Norte",
        "LAGUNA": "Laguna",
    }

    # Nombre de la tabla
    __tablename__ = "incapacidades"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="incapacidades")

    # Columnas
    fecha_inicio: Mapped[date]
    fecha_termino: Mapped[date]
    clave_incapacidad: Mapped[str] = mapped_column(String(32))
    region: Mapped[str] = mapped_column(Enum(*REGIONES, name="incapacidades_regiones", native_enum=False), index=True)
    motivo: Mapped[str] = mapped_column(String(128))
    puesto_nombre: Mapped[str] = mapped_column(String(128))

    def __repr__(self):
        """Representación"""
        return f"<Incapacidad {self.id}>"
