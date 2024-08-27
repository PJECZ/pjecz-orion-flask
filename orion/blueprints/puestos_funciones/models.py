"""
Puestos Funciones, modelos
"""

from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PuestoFuncion(database.Model, UniversalMixin):
    """PuestoFuncion"""

    # Nombre de la tabla
    __tablename__ = "puestos_funciones"

    # Clave foránea
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puestos.id"))
    puesto: Mapped["Puesto"] = relationship(back_populates="puestos_funciones")

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(128))

    # Hijos
    historial_puestos: Mapped[List["HistorialPuesto"]] = relationship(back_populates="puesto_funcion")
    atribuciones: Mapped[List["Atribucion"]] = relationship(back_populates="funcion")

    def __repr__(self):
        """Representación"""
        return f"<PuestoFuncion {self.id}>"
