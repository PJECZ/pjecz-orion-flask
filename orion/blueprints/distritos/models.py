"""
Distritos, modelos
"""

from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Distrito(database.Model, UniversalMixin):
    """Distrito"""

    # Nombre de la tabla
    __tablename__ = "distritos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(16), unique=True)
    nombre: Mapped[str] = mapped_column(String(256))

    # Hijos
    # centros_trabajos = db.relationship("CentroTrabajo", back_populates="distrito")

    @property
    def nombre_descriptivo(self):
        """Junta nombre del curso y su descripción"""
        return self.clave + ": " + self.nombre

    def __repr__(self):
        """Representación"""
        return f"<Distrito {self.id}>"
