"""
Carreras, modelos
"""

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Carrera(database.Model, UniversalMixin):
    """Carrera"""

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
