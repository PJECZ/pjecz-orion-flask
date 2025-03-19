"""
Personas Actas Protestas, modelos
"""

from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PersonaActaProtesta(database.Model, UniversalMixin):
    """PersonaActaProtesta"""

    # https://developer.mozilla.org/es/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
    EXTENSIONES = {
        "jpg": ("Imagen", "image/jpg"),
        "jpeg": ("Imagen", "image/jpeg"),
        "png": ("Imagen", "image/png"),
        "pdf": ("Archivo PDF", "application/pdf"),
        "docx": ("Archivo Word", "application/msword"),
    }

    # Nombre de la tabla
    __tablename__ = "personas_actas_protestas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="personas_actas_protestas")

    # Columnas
    fecha: Mapped[date] = mapped_column(Date, default=now())
    cargo: Mapped[Optional[str]] = mapped_column(String(256))
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
        extensiones_permitidas = PersonaActaProtesta.EXTENSIONES.keys()
        if "." in archivo_nombre and archivo_nombre.rsplit(".", 1)[1] in extensiones_permitidas:
            self.extension = archivo_nombre.rsplit(".", 1)[1]
            return True
        return False

    def __repr__(self):
        """Representación"""
        return f"<PersonaActaProtesta {self.id}>"
