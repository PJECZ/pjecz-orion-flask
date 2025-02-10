"""
Municipios, modelos
"""

from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Municipio(database.Model, UniversalMixin):
    """Municipio"""

    # Nombre de la tabla
    __tablename__ = "municipios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(3))
    nombre: Mapped[str] = mapped_column(String(256))

    # Hijos
    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="municipio")

    @property
    def clave_nombre(self):
        """Regresa la clave y el nombre"""
        return self.clave + ": " + self.nombre

    def __repr__(self):
        """Representación"""
        return f"<Municipio {self.id}>"
