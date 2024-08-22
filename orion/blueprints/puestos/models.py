"""
Puestos, modelos
"""

from typing import List

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Puesto(database.Model, UniversalMixin):
    """Puesto"""

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

    TIPOS_EMPLEADOS = {
        "CONF": "CONF: Confianza",
        "BASE": "BASE: Base",
        "SIND": "SIND: Sindicalizado",
    }

    # Nombre de la tabla
    __tablename__ = "puestos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    clave: Mapped[str] = mapped_column(String(32), unique=True)
    nombre: Mapped[str] = mapped_column(String(128))
    tipo_cargo: Mapped[str] = mapped_column(Enum(*CARGOS, name="puestos_cargos", native_enum=False), index=True)
    tipo_empleado: Mapped[str] = mapped_column(
        Enum(*TIPOS_EMPLEADOS, name="puestos_tipos_empleados", native_enum=False), index=True
    )

    # Hijos
    puestos_funciones: Mapped[List["PuestoFuncion"]] = relationship(back_populates="puesto")
    # personas_meritos = db.relationship("PersonaMerito", back_populates="puesto")
    # personas_escalafones_del_cargo_de = db.relationship("PersonaEscalafon", foreign_keys="PersonaEscalafon.del_cargo_de_id")
    # personas_escalafones_al_cargo_de = db.relationship("PersonaEscalafon", foreign_keys="PersonaEscalafon.al_cargo_de_id")

    @property
    def clave_nombre(self):
        """Junta la clave y el nombre"""
        return self.clave + ": " + self.nombre

    def __repr__(self):
        """Representación"""
        return f"<Puesto {self.id}>"
