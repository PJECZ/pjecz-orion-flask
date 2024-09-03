"""
Historial Académicos, modelos
"""

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class HistorialAcademico(database.Model, UniversalMixin):
    """HistorialAcademico"""

    # Nombre de la tabla
    __tablename__ = "historial_academicos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="historial_academicos")
    nivel_academico_id: Mapped[int] = mapped_column(ForeignKey("niveles_academicos.id"))
    nivel_academico: Mapped["NivelAcademico"] = relationship(back_populates="historial_academicos")

    # Columnas
    nombre_escuela: Mapped[Optional[str]] = mapped_column(String(64))
    nombre_ciudad: Mapped[Optional[str]] = mapped_column(String(64))
    ano_inicio: Mapped[Optional[int]]
    ano_termino: Mapped[Optional[int]]
    # cedula_profesional: Mapped[Optional[str]] = mapped_column(String(16))

    def __repr__(self):
        """Representación"""
        return f"<HistorialAcademico {self.id}>"
