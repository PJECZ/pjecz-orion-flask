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

    def __repr__(self):
        """Representación"""
        return f"<Municipio {self.id}>"
