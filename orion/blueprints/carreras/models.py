"""
Carreras, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Carrera(database.Model, UniversalMixin):
    """Carrera"""

    ESTADOS = {
        "PENDIENTE": "Pendiente",
        "CANCELADO": "Cancelado",
    }

    # Nombre de la tabla
    __tablename__ = "carreras"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(128), unique=True)

    # Hijos
    personas: Mapped[List["Persona"]] = relationship("Persona", back_populates="carrera")

    def __repr__(self):
        """Representación"""
        return f"<Carrera {self.id}>"
