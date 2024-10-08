"""
Niveles Académicos, modelos
"""

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class NivelAcademico(database.Model, UniversalMixin):
    """NivelAcademico"""

    # Nombre de la tabla
    __tablename__ = "niveles_academicos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(8), unique=True)
    nombre: Mapped[str] = mapped_column(String(64))

    # Hijos
    personas: Mapped[List["Persona"]] = relationship("Persona", back_populates="nivel_estudios_max")
    historial_academicos: Mapped[List["HistorialAcademico"]] = relationship(back_populates="nivel_academico")

    @property
    def clave_nombre(self):
        """Junta la clave y el nombre"""
        return self.clave + ": " + self.nombre

    def __repr__(self):
        """Representación"""
        return f"<NivelAcademico {self.id}>"
