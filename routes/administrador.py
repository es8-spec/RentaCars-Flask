import os

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from database import mysql

administrador = Blueprint("administrador", __name__)


def _require_admin():
    if "id" not in session:
        return redirect(url_for("acceso.index"))
    if session.get("rol") != "Administrador":
        return redirect(url_for("acceso.index"))
    return None


@administrador.route("/administrador")
def dashboard():
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login
    return render_template("administrador/dashboard.html")


@administrador.route("/perfil")
def perfil():
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login
    return render_template("administrador/perfil.html")


@administrador.route("/agregar_vehiculo", methods=["GET", "POST"])
def agregar_vehiculo():
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    mensaje = ""
    tipo_mensaje = ""

    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        anio = request.form["anio"]
        placa = request.form["placa"]
        precio = request.form["precio"]
        imagen = request.files["imagen"]

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM vehiculos WHERE placa = %s", (placa,))
        vehiculo = cursor.fetchone()

        if vehiculo:
            mensaje = "La placa ya está registrada."
            tipo_mensaje = "danger"
        else:
            nombre_imagen = ""
            if imagen.filename != "":
                nombre_imagen = secure_filename(imagen.filename)
                ruta = os.path.join("static", "subidos", "vehiculos", nombre_imagen)
                imagen.save(ruta)

            sql = "INSERT INTO vehiculos(marca, modelo, anio, placa, precio, imagen) VALUES(%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (marca, modelo, anio, placa, precio, nombre_imagen))
            mysql.connection.commit()
            mensaje = "Vehículo registrado correctamente."
            tipo_mensaje = "success"

        cursor.close()

    return render_template("administrador/agregar_vehiculo.html", mensaje=mensaje, tipo_mensaje=tipo_mensaje)


@administrador.route("/listar_vehiculos")
def listar_vehiculos():
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, marca, modelo, anio, placa, precio, imagen, estado FROM vehiculos ORDER BY id DESC")
    vehiculos = cursor.fetchall()
    cursor.close()
    return render_template("administrador/listar_vehiculos.html", vehiculos=vehiculos)


@administrador.route("/editar_vehiculo/<int:id>", methods=["GET", "POST"])
def editar_vehiculo(id):
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    mensaje = ""
    tipo_mensaje = ""

    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        anio = request.form["anio"]
        placa = request.form["placa"]
        precio = request.form["precio"]
        imagen = request.files["imagen"]

        cursor.execute("SELECT id FROM vehiculos WHERE placa = %s AND id <> %s", (placa, id))
        vehiculo_existente = cursor.fetchone()

        if vehiculo_existente:
            mensaje = "La placa ya está registrada en otro vehículo."
            tipo_mensaje = "danger"
        else:
            if imagen.filename != "":
                nombre_imagen = secure_filename(imagen.filename)
                ruta = os.path.join("static", "subidos", "vehiculos", nombre_imagen)
                imagen.save(ruta)
                cursor.execute(
                    "UPDATE vehiculos SET marca=%s, modelo=%s, anio=%s, placa=%s, precio=%s, imagen=%s WHERE id=%s",
                    (marca, modelo, anio, placa, precio, nombre_imagen, id),
                )
            else:
                cursor.execute(
                    "UPDATE vehiculos SET marca=%s, modelo=%s, anio=%s, placa=%s, precio=%s WHERE id=%s",
                    (marca, modelo, anio, placa, precio, id),
                )

            mysql.connection.commit()
            mensaje = "Vehículo actualizado correctamente."
            tipo_mensaje = "success"

    cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (id,))
    vehiculo = cursor.fetchone()
    cursor.close()
    return render_template("administrador/editar_vehiculo.html", vehiculo=vehiculo, mensaje=mensaje, tipo_mensaje=tipo_mensaje)


@administrador.route("/eliminar_vehiculo/<int:id>")
def eliminar_vehiculo(id):
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT imagen FROM vehiculos WHERE id = %s", (id,))
    vehiculo = cursor.fetchone()
    if vehiculo:
        nombre_imagen = vehiculo[0]
        if nombre_imagen:
            ruta = os.path.join("static", "subidos", "vehiculos", nombre_imagen)
            if os.path.exists(ruta):
                os.remove(ruta)
        cursor.execute("DELETE FROM vehiculos WHERE id = %s", (id,))
        mysql.connection.commit()
    cursor.close()
    return redirect(url_for("administrador.listar_vehiculos"))


@administrador.route("/vehiculos_rentados")
def vehiculos_rentados():
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    sql = """
    SELECT
        rentas.id,
        usuarios.cedula,
        usuarios.nombres,
        usuarios.apellidos,
        vehiculos.marca,
        vehiculos.modelo,
        vehiculos.placa,
        rentas.fecha_renta,
        rentas.pagado
    FROM rentas
    INNER JOIN usuarios ON rentas.id_usuario = usuarios.id
    INNER JOIN vehiculos ON rentas.id_vehiculo = vehiculos.id
    ORDER BY rentas.id DESC
    """
    cursor.execute(sql)
    rentas = cursor.fetchall()
    cursor.close()
    return render_template("administrador/vehiculos_rentados.html", rentas=rentas)


@administrador.route("/ver_comprobante/<int:id>")
def ver_comprobante(id):
    redirect_to_login = _require_admin()
    if redirect_to_login is not None:
        return redirect_to_login

    cursor = mysql.connection.cursor()
    sql = """
    SELECT
        usuarios.cedula,
        usuarios.nombres,
        usuarios.apellidos,
        usuarios.telefono,
        vehiculos.marca,
        vehiculos.modelo,
        vehiculos.anio,
        vehiculos.placa,
        vehiculos.precio,
        vehiculos.imagen,
        rentas.fecha_renta,
        rentas.pagado,
        rentas.cedula
    FROM rentas
    INNER JOIN usuarios ON rentas.id_usuario = usuarios.id
    INNER JOIN vehiculos ON rentas.id_vehiculo = vehiculos.id
    WHERE rentas.id = %s
    """
    cursor.execute(sql, (id,))
    comprobante = cursor.fetchone()
    cursor.close()
    if comprobante is None:
        return redirect(url_for("administrador.vehiculos_rentados"))
    return render_template("administrador/ver_comprobante.html", comprobante=comprobante)
