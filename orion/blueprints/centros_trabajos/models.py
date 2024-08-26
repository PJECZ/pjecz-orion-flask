"""
Centros de Trabajos, modelos
"""

from typing import List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class CentroTrabajo(database.Model, UniversalMixin):
    """CentroTrabajo"""

    # Nombre de la tabla
    __tablename__ = "centros_trabajos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    distrito_id: Mapped[int] = mapped_column(ForeignKey("distritos.id"))
    distrito: Mapped["Distrito"] = relationship(back_populates="centros_trabajos")
    organo_id: Mapped[int] = mapped_column(ForeignKey("organos.id"))
    organo: Mapped["Organo"] = relationship(back_populates="centros_trabajos")

    # Columnas
    clave: Mapped[str] = mapped_column(String(16), unique=True)
    nombre: Mapped[str] = mapped_column(String(128))
    telefono: Mapped[Optional[str]] = mapped_column(String(128))
    num_ext: Mapped[Optional[str]] = mapped_column(String(64))
    activo: Mapped[bool] = mapped_column(default=False)

    # Hijos
    # TODO: Conectar Hijos
    areas: Mapped[List["Area"]] = relationship(back_populates="centro_trabajo")
    # atribuciones = db.relationship("Atribucion", back_populates="centro_trabajo")

    @property
    def clave_nombre(self):
        """Regresa la clave y el nombre"""
        return self.clave + ": " + self.nombre

    def __repr__(self):
        """Representación"""
        return f"<CentroTrabajo {self.id}>"
