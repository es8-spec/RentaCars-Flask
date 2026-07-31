try:
    from flask_mysqldb import MySQL
except ImportError:  # pragma: no cover - fallback para desarrollo local sin módulo instalado
    class MySQL:
        def init_app(self, app):
            return None

        @property
        def connection(self):
            raise RuntimeError("Flask-MySQLdb no está instalado. Instálalo con pip install flask-mysqldb")


mysql = MySQL()
