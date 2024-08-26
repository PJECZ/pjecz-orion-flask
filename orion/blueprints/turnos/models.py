"""
Turnos, modelos
"""

from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Turno(database.Model, UniversalMixin):
    """Turno"""

    # Nombre de la tabla
    __tablename__ = "turnos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(64), unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(64))

    # Hijos
    historial_puestos: Mapped[List["HistorialPuesto"]] = relationship(back_populates="turno")

    def __repr__(self):
        """Representación"""
        return f"<Turno {self.id}>"
