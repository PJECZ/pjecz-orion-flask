"""
Áreas, modelos
"""

from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Area(database.Model, UniversalMixin):
    """Area"""

    # Nombre de la tabla
    __tablename__ = "areas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    centro_trabajo_id: Mapped[int] = mapped_column(ForeignKey("centros_trabajos.id"))
    centro_trabajo: Mapped["CentroTrabajo"] = relationship(back_populates="areas")

    # Columnas
    nombre: Mapped[str] = mapped_column(String(128), unique=True)

    # Hijos
    atribuciones_ct: Mapped[List["AtribucionCT"]] = relationship(back_populates="area")

    def __repr__(self):
        """Representación"""
        return f"<Area {self.id}>"
