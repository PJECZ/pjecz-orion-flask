"""
Atribuciones, modelos
"""

from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Atribucion(database.Model, UniversalMixin):
    """Atribucion"""

    CARGOS = {
        "A": "A: Administrativo",
        "AC": "AC: Actuario",
        "D": "D: Defensor",
        "JPI": "JPI: Juez Primera Instancia",
        "MTAA": "MTAA: Magistrado del Tribunal de Apelación de Adolecentes",
        "MTCA": "MTCA: Magistrado del Tribunal de Concilación y Arbitraje",
        "MTD": "MTD: Magistrado Distrital",
        "MTSJ": "MTSJ: Magistrado TSJ",
        "S": "S: Secretario",
    }

    # Nombre de la tabla
    __tablename__ = "atribuciones"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    funcion_id: Mapped[int] = mapped_column(ForeignKey("puestos_funciones.id"))
    funcion: Mapped["PuestoFuncion"] = relationship(back_populates="atribuciones")
    centro_trabajo_id: Mapped[int] = mapped_column(ForeignKey("centros_trabajos.id"))
    centro_trabajo: Mapped["CentroTrabajo"] = relationship(back_populates="atribuciones")

    # Columnas
    norma: Mapped[str] = mapped_column(String(512))
    fundamento: Mapped[str] = mapped_column(String(512))
    fragmento: Mapped[str] = mapped_column(String(512))
    tipo_cargo: Mapped[Optional[str]] = mapped_column(Enum(*CARGOS, name="atribuciones_cargos", native_enum=False), index=True)

    def __repr__(self):
        """Representación"""
        return f"<Atribucion {self.id}>"
