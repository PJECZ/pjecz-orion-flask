"""
Atribuciones CT (Centros de Trabajo), modelos
"""

from typing import List

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class AtribucionCT(database.Model, UniversalMixin):
    """AtribucionCT"""

    # Nombre de la tabla
    __tablename__ = "atribuciones_ct"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    area: Mapped["Area"] = relationship(back_populates="atribuciones_ct")

    # Columnas
    norma: Mapped[str] = mapped_column(String(512))
    fundamento: Mapped[str] = mapped_column(String(512))
    fragmento: Mapped[str] = mapped_column(String(512))

    def __repr__(self):
        """Representación"""
        return f"<AtribucionCT {self.id}>"
