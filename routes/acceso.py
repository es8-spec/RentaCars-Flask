from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import mysql

acceso = Blueprint("acceso", __name__)


@acceso.route("/")
def index():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total = cursor.fetchone()
        cursor.close()
        total_usuarios = total[0] if total else 0
    except Exception:
        total_usuarios = 0

    return render_template("acceso/index.html", total_usuarios=total_usuarios)


@acceso.route("/registro", methods=["GET", "POST"])
def registro():
    mensaje = ""
    tipo_mensaje = ""

    if request.method == "POST":
        cedula = request.form["cedula"]
        nombres = request.form["nombres"]
        apellidos = request.form["apellidos"]
        telefono = request.form["telefono"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE cedula = %s", (cedula,))
        usuario = cursor.fetchone()

        if usuario:
            mensaje = "La cédula ya está registrada."
            tipo_mensaje = "danger"
        else:
            password_encriptado = generate_password_hash(password)
            sql = "INSERT INTO usuarios(cedula, nombres, apellidos, telefono, password, rol) VALUES(%s, %s, %s, %s, %s, 'Cliente')"
            cursor.execute(sql, (cedula, nombres, apellidos, telefono, password_encriptado))
            mysql.connection.commit()
            mensaje = "Usuario registrado correctamente."
            tipo_mensaje = "success"

        cursor.close()

    return render_template("acceso/registro.html", mensaje=mensaje, tipo_mensaje=tipo_mensaje)


@acceso.route("/iniciar_sesion", methods=["GET", "POST"])
def iniciar_sesion():
    mensaje = ""

    if request.method == "POST":
        cedula = request.form["cedula"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, nombres, apellidos, password, rol FROM usuarios WHERE cedula = %s", (cedula,))
        usuario = cursor.fetchone()

        if usuario:
            password_bd = usuario[3]
            # Sanitize stored hash: remove surrounding whitespace and quotes
            try:
                if isinstance(password_bd, bytes):
                    password_bd = password_bd.decode('utf-8', errors='ignore')
                password_bd = password_bd.strip().strip('"\'"')
            except Exception:
                password_bd = str(password_bd)

            # Now verify password; if stored hash malformed, handle error
            try:
                valid = check_password_hash(password_bd, password)
            except Exception:
                valid = False

            if valid:
                session["id"] = usuario[0]
                session["nombre"] = f"{usuario[1]} {usuario[2]}"
                session["rol"] = usuario[4]
                cursor.close()
                if usuario[4] == "Administrador":
                    return redirect(url_for("administrador.dashboard"))
                return redirect(url_for("cliente.dashboard"))
            else:
                mensaje = "Contraseña incorrecta."
        else:
            mensaje = "La cédula no está registrada."

        cursor.close()

    return render_template("acceso/login.html", mensaje=mensaje)


@acceso.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("acceso.index"))
