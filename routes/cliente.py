import os

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from database import mysql

cliente = Blueprint("cliente", __name__)


def _require_client():
    if "id" not in session:
        return redirect(url_for("acceso.index"))
    if session.get("rol") != "Cliente":
        return redirect(url_for("acceso.index"))
    return None


@cliente.route("/cliente")
def dashboard():
    redirect_to_login = _require_client()
    if redirect_to_login is not None:
        return redirect_to_login
    return render_template("cliente/dashboard.html")


@cliente.route("/perfil_cliente")
def perfil():
    redirect_to_login = _require_client()
    if redirect_to_login is not None:
        return redirect_to_login
    return render_template("cliente/perfil.html")


@cliente.route("/ver_vehiculos")
def ver_vehiculos():
    redirect_to_login = _require_client()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, marca, modelo, anio, placa, precio, imagen FROM vehiculos WHERE estado = 'Disponible' ORDER BY marca")
    vehiculos = cursor.fetchall()
    cursor.close()
    return render_template("cliente/ver_vehiculos.html", vehiculos=vehiculos)


@cliente.route("/rentar_vehiculo/<int:id>", methods=["GET", "POST"])
def rentar_vehiculo(id):
    redirect_to_login = _require_client()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (id,))
    vehiculo = cursor.fetchone()
    if vehiculo is None:
        cursor.close()
        return redirect(url_for("cliente.ver_vehiculos"))

    mensaje = ""
    tipo_mensaje = ""

    if request.method == "POST":
        fecha_renta = request.form["fecha_renta"]
        archivo = request.files["cedula"]
        nombre_archivo = ""

        if archivo.filename != "":
            nombre_archivo = secure_filename(archivo.filename)
            archivo.save(os.path.join("static", "subidos", "cedulas", nombre_archivo))

        sql = "INSERT INTO rentas(id_usuario, id_vehiculo, cedula, fecha_renta) VALUES(%s, %s, %s, %s)"
        cursor.execute(sql, (session["id"], id, nombre_archivo, fecha_renta))
        cursor.execute("UPDATE vehiculos SET estado='Rentado' WHERE id=%s", (id,))
        mysql.connection.commit()
        mensaje = "Vehículo rentado correctamente."
        tipo_mensaje = "success"

    cursor.close()
    return render_template("cliente/rentar_vehiculo.html", vehiculo=vehiculo, mensaje=mensaje, tipo_mensaje=tipo_mensaje)


@cliente.route("/historial_rentas")
def historial_rentas():
    redirect_to_login = _require_client()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    sql = """
    SELECT
        rentas.id,
        vehiculos.marca,
        vehiculos.modelo,
        vehiculos.placa,
        vehiculos.imagen,
        rentas.fecha_renta,
        rentas.pagado
    FROM rentas
    INNER JOIN vehiculos ON rentas.id_vehiculo = vehiculos.id
    WHERE rentas.id_usuario = %s
    ORDER BY rentas.id DESC
    """
    cursor.execute(sql, (session["id"],))
    rentas = cursor.fetchall()
    cursor.close()
    return render_template("cliente/historial_rentas.html", rentas=rentas)
