"""
Personas Archivos Adjuntos, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PersonaAdjunto(database.Model, UniversalMixin):
    """PersonaAdjunto"""

    TIPOS = {
        "INE": "INE",
        "ACTA_NAC": "Acta de Nacimiento",
        "CEDULA_PROF": "Cédula Profesional",
        "CONST_SIT_FIS": "Constancia de Situación Fiscal",
        "CREDENCIAL_PJ": "Credencial del Poder Judicial",
        "CURP": "CURP",
        "NOMBRAMIENTO": "Nombramiento",
        "TITUTLO": "Título",
        "OTRO": "Otro",
    }

    # Nombre de la tabla
    __tablename__ = "personas_adjuntos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="adjuntos")

    # Columnas
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS, name="personas_adjuntos_tipos", native_enum=False), index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(128))
    archivo: Mapped[Optional[str]] = mapped_column(String(64))
    url: Mapped[Optional[str]] = mapped_column(String(512))

    # Variables
    extension = ""

    @staticmethod
    def type_format(file_name):
        "Tipo de formato del archivo"
        try:
            extension = file_name.rsplit(".", 1)[1]
        except:
            return ""
        if extension in ("jpg", "jpeg", "png"):
            return "IMG"
        if extension in ("docx", "xlsx"):
            return "DOC"
        if extension == "pdf":
            return "PDF"
        return ""

    def set_extension(self, archivo_nombre):
        """Establece el tipo de extensión del archivo"""
        extensiones_permitidas = PersonaNombramiento.EXTENSIONES.keys()
        if "." in archivo_nombre and archivo_nombre.rsplit(".", 1)[1] in extensiones_permitidas:
            self.extension = archivo_nombre.rsplit(".", 1)[1]
            return True
        return False

    def __repr__(self):
        """Representación"""
        return f"<PersonaAdjunto {self.id}>"
