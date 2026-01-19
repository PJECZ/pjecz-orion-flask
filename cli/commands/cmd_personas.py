"""
CLI Personas
"""

import sys
import csv
from pathlib import Path

import click

from orion.app import create_app
from orion.blueprints.personas.models import Persona
from orion.extensions import database

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Personas"""


@click.command()
@click.argument("archivo_csv", type=str)
@click.option("--simulacion", default=True, help="Simula cuantos y cuales cambios se harán.")
def actualizar_correos_csv(archivo_csv, simulacion):
    """Actualizar correo de personas desde un archivo CSV"""
    ruta = Path(archivo_csv)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        sys.exit(1)
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        sys.exit(1)

    if simulacion:
        click.echo("Iniciando simulación de actualización de correos")
    else:
        click.echo("Iniciando actualización de correos")

    contador = 0
    errores = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            persona_curp = row["CURP"]
            persona_email = row["CORREO"]
            persona = Persona.query.filter_by(curp=persona_curp).first()
            if persona is None:
                click.echo(click.style(f"AVISO: {persona_curp} NO existe", fg="red"))
                errores += 1
                continue
            if persona.email != persona_email:
                contador += 1
                click.echo(f"CAMBIO EN PERSONA: {persona.email} -> {persona_email}")
                if simulacion is False:
                    persona.email = persona_email
                    persona.save()
    click.echo()
    click.echo(click.style(f"= {contador} cambios realizados.", fg="green"))
    click.echo(click.style(f"= {errores} errores encontrados.", fg="red"))


cli.add_command(actualizar_correos_csv)
