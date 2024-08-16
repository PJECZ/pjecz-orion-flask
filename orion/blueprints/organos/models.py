"""
Órganos, modelos
"""

from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Organo(database.Model, UniversalMixin):
    """Organo"""

    # Nombre de la tabla
    __tablename__ = "organos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(16), unique=True)
    nombre: Mapped[str] = mapped_column(String(64))

    # Hijos
    centros_trabajos: Mapped[List["CentroTrabajo"]] = relationship(back_populates="organo")

    @property
    def nombre_descriptivo(self):
        """Clave y Nombre"""
        return f"{self.clave}: {self.nombre}"

    def __repr__(self):
        """Representación"""
        return f"<Organo {self.id}>"
