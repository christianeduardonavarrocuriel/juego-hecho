"""
Aplicación web.py servida con Waitress.

Notas:
- Para ejecutarla con Waitress desde la raíz del proyecto:
        waitress-serve --listen=*:8080 app:application
- Usamos ruta absoluta para las plantillas para que funcione sin importar desde dónde se ejecute.
"""

import os
import web
import logging
import sqlite3

# Configurar logging
logging.getLogger('waitress.queue').setLevel(logging.ERROR)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

render = web.template.render(TEMPLATES_DIR, cache=False)

def conectar_db():
    db_path = os.path.join(BASE_DIR, 'registro.db')
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tutores (
            id_tutor INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ninos (
            id_nino INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tutor INTEGER NOT NULL,
            genero TEXT NOT NULL CHECK(genero IN ('Ajolotito','Ajolotita')),
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            password_figuras TEXT NOT NULL,
            FOREIGN KEY (id_tutor) REFERENCES tutores(id_tutor) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

init_db()

# ---------------- CLASES ----------------
urls = (
    '/', 'Index',
    '/registrar_tutor', 'RegistrarTutor',
    '/registrar_chiquillo', 'RegistrarChiquillo',
    '/inicio_administrador', 'InicioAdministrador',
    '/saludo_admin', 'SaludoAdmin',
    '/saludo_chiquillo', 'SaludoChiquillo',
    '/presentacion_lucas', 'PresentacionLucas',
    '/presentacion_pagina', 'PresentacionPagina',
    '/lecciones', 'Lecciones',
    '/perfil_admin', 'PerfilAdmin',
    '/perfil_chiquillo', 'PerfilChiquillo',
    '/editar_perfil', 'EditarPerfil',
    '/iniciar_sesion', 'IniciarSesion',
    '/quienes_somos', 'QuienesSomos',
    '/introduccion', 'Introduccion',
    '/leccion_coordinacion', 'LeccionCoordinacion',
    '/leccion_completada', 'LeccionCompletada',
    '/favicon.ico', 'Favicon',
    '/static/(.*)', 'StaticFiles',
)
class Index:
    def GET(self):
        return render.index()

class RegistrarTutor:
    def GET(self):
        return render.registrar_tutor()

    def POST(self):
        data = web.input()
        print("Datos del tutor recibidos:", dict(data))
        nombres = data.get('nombre','').strip()
        apellidos = data.get('primer_apellido_y_segundo_apellido','').strip()
        correo = data.get('correo_tutor','').strip().lower()
        password = data.get('contraseña','').strip()
        rol = data.get('tipo_usuario','').strip()
        if not all([nombres, apellidos, correo, password, rol]):
            return "Error: Todos los campos son obligatorios."
        if len(password) != 6:
            return "Error: La contraseña debe tener exactamente 6 caracteres."
        if '@' not in correo or '.' not in correo:
            return "Error: Formato de correo inválido."
        try:
            conn = conectar_db(); cur = conn.cursor()
            if rol.lower() in ['padre','madre','padre/madre']:
                rol_normalizado = 'Padre'
            elif rol.lower()=='tutor':
                rol_normalizado='Tutor'
            elif rol.lower()=='maestro':
                rol_normalizado='Maestro'
            else:
                rol_normalizado='Padre'
            cur.execute('''INSERT INTO tutores (rol,nombres,apellidos,correo,password) VALUES (?,?,?,?,?)''',
                        (rol_normalizado,nombres,apellidos,correo,password))
            tutor_id = cur.lastrowid
            conn.commit(); conn.close()
            session.tutor_id = tutor_id
            print(f"✅ Tutor registrado: {tutor_id} {nombres} {apellidos} {rol_normalizado}")
            raise web.seeother('/registrar_chiquillo')
        except sqlite3.IntegrityError:
            try: conn.rollback(); conn.close()
            except Exception: pass
            return "Error: El correo ya está registrado."
        except web.HTTPError:
            raise
        except Exception as e:
            try: conn.rollback(); conn.close()
            except Exception: pass
            print("❌ Error tutor:", e)
            return "Error al registrar el tutor."

class RegistrarChiquillo:
    def GET(self):
        return render.registrar_chiquillo()

    def POST(self):
        data = web.input()
        print("Datos recibidos registrar_chiquillo:", dict(data))
        tutor_id = session.get('tutor_id', None)
        if not tutor_id:
            try:
                cconn = conectar_db(); ccur = cconn.cursor();
                ccur.execute('SELECT MAX(id_tutor) FROM tutores'); row = ccur.fetchone(); cconn.close()
                tutor_id = row[0] if row and row[0] else None
                if tutor_id: session.tutor_id = tutor_id
            except Exception as e:
                print('Error fallback tutor:', e)
                return 'Error: Registre primero al tutor.'
        if not tutor_id:
            return 'Error: No hay tutor asociado.'
        indices = []
        for k in data.keys():
            if k.startswith('nombre_'):
                try:
                    num = int(k.split('_')[1])
                    if num not in indices: indices.append(num)
                except ValueError: pass
        indices.sort()
        if not indices:
            return 'Error: No se recibieron niños.'
        permitidos = {'ajolote','borrego','oso','perro'}
        registros = []
        try:
            conn = conectar_db(); cur = conn.cursor()
            for idx in indices:
                nombre = data.get(f'nombre_{idx}','').strip()
                apellidos = data.get(f'apellidos_{idx}','').strip()
                genero = data.get(f'tipo_usuario_{idx}','').strip()
                password_raw = data.get(f'contraseña_{idx}','').strip()
                if not all([nombre, apellidos, genero, password_raw]):
                    return f'Error: Faltan datos en Niño {idx}.'
                if genero not in ['Ajolotito','Ajolotita']:
                    return f'Error: Género inválido en Niño {idx}.'
                animales = [a for a in password_raw.split(',') if a]
                if len(animales) != 6:
                    return f'Error: La contraseña del Niño {idx} debe tener exactamente 6 animales.'
                if any(a not in permitidos for a in animales):
                    return f'Error: Niño {idx} tiene animales no permitidos.'
                password_figuras = ','.join(animales)
                cur.execute('''INSERT INTO ninos (id_tutor,genero,nombres,apellidos,password_figuras) VALUES (?,?,?,?,?)''',
                            (tutor_id, genero, nombre, apellidos, password_figuras))
                registros.append((cur.lastrowid, nombre))
            conn.commit(); conn.close()
            print('✅ Niños insertados:', registros, 'Tutor', tutor_id)
            raise web.seeother('/saludo_admin')
        except web.HTTPError:
            raise
        except Exception as e:
            print('❌ Error registrando niños:', e)
            try: conn.rollback(); conn.close()
            except Exception: pass
            return 'Error al registrar los niños.'
        data = web.input()
        print("Datos recibidos en registrar_chiquillo (raw):", dict(data))

        # Obtener tutor_id de la sesión o fallback al último
        tutor_id = session.get('tutor_id', None)
        if not tutor_id:
            try:
                conn_tmp = conectar_db()
                cur_tmp = conn_tmp.cursor()
                cur_tmp.execute('SELECT MAX(id_tutor) FROM tutores')
                row = cur_tmp.fetchone()
                tutor_id = row[0] if row and row[0] else None
                conn_tmp.close()
                if tutor_id:
                    session.tutor_id = tutor_id
                    print(f"Tutor asociado (fallback) -> {tutor_id}")
            except Exception as e:
                print(f"Error obteniendo tutor_id: {e}")
                return "Error: No se pudo asociar el niño con un tutor."

        if not tutor_id:
            return "Error: No hay tutor asociado. Registra primero un tutor."

        # Detectar múltiples niños: campos nombre_1, nombre_2, ...
        inserted = 0
        errores = []

        try:
            conn = conectar_db()
            cursor = conn.cursor()

            index = 1
            while True:
                nombre_key = f'nombre_{index}'
                if nombre_key not in data:
                    break
                nombres = data.get(nombre_key, '').strip()
                apellidos = data.get(f'apellidos_{index}', '').strip()
                genero_raw = data.get(f'tipo_usuario_{index}', '').strip()
                password_animales = data.get(f'contraseña_{index}', '').strip()

                if not (nombres and apellidos and genero_raw and password_animales):
                    errores.append(f"Niño {index}: campos incompletos")
                    index += 1
                    continue

                # Normalizar genero (capitalizar)
                genero = genero_raw.capitalize()
                if genero not in ['Ajolotito', 'Ajolotita']:
                    errores.append(f"Niño {index}: género inválido {genero_raw}")
                    index += 1
                    continue

                # Validar contraseña (exactamente 6 animales separados por comas)
                animales = [a for a in password_animales.split(',') if a]
                if len(animales) != 6:
                    errores.append(f"Niño {index}: contraseña debe tener 6 animales (tiene {len(animales)})")
                    index += 1
                    continue

                cursor.execute('''
                    INSERT INTO ninos (id_tutor, genero, nombres, apellidos, password_figuras)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tutor_id, genero, nombres, apellidos, password_animales))
                inserted += 1
                print(f"✅ Insertado Niño {index}: {nombres} {apellidos} ({genero}) - Tutor {tutor_id}")
                index += 1

            conn.commit()
            conn.close()
        except sqlite3.IntegrityError as e:
            print(f"Error de integridad al insertar niños: {e}")
            return "Error: No se pudieron registrar los niños (integridad)."
        except Exception as e:
            print(f"Error general al insertar niños: {e}")
            return "Error al registrar los niños. Intenta de nuevo."

        if inserted == 0:
            return "Error: No se registró ningún niño. " + ('; '.join(errores) if errores else '')

        print(f"Resumen registro niños -> insertados: {inserted}; errores: {len(errores)}")
        raise web.seeother('/saludo_admin')

class DebugNinos:
    def GET(self):
        try:
            conn = conectar_db()
            cur = conn.cursor()
            cur.execute('''SELECT n.id_nino, n.nombres, n.apellidos, n.genero, n.password_figuras, n.id_tutor,
                                  t.nombres, t.apellidos, t.rol
                           FROM ninos n LEFT JOIN tutores t ON n.id_tutor = t.id_tutor
                           ORDER BY n.id_nino DESC''')
            rows = cur.fetchall()
            conn.close()
            html = ["<h2>Niños registrados</h2>", f"<p>Total: {len(rows)}</p>", '<table border=1 cellpadding=5>']
            html.append('<tr><th>ID</th><th>Nombres</th><th>Apellidos</th><th>Género</th><th>Password</th><th>Tutor ID</th><th>Tutor</th><th>Rol</th></tr>')
            for r in rows:
                html.append(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]} {r[7]}</td><td>{r[8]}</td></tr>")
            html.append('</table>')
            return '\n'.join(html)
        except Exception as e:
            return f"Error debug: {e}"

class SaludoAdmin:
    def GET(self):
        return render.saludo_admin()

class PerfilAdmin:
    def GET(self):
        # Datos de prueba para evitar el error
        tutor_prueba = {
            'nombres': 'Usuario',
            'apellidos': 'Prueba',
            'correo': 'usuario@ejemplo.com',
            'rol': 'Padre/Madre'
        }
        ninos_prueba = [
            {
                'nombres': 'Niño',
                'apellidos': 'Ejemplo',
                'genero': 'Ajolotito',
                'password_figuras': 'abc123'
            }
        ]
        return render.perfil_admin(tutor_prueba, ninos_prueba)

class PerfilChiquillo:
    def GET(self):
        return render.perfil_chiquillo()

class IniciarSesion:
    def GET(self):
        return render.iniciar_sesion()

    def POST(self):
        data = web.input()
        nombre = data.get('nombre','').strip()
        apellidos = data.get('primer_apellido-y-segundo-apellido','').strip()
        password_animales = (data.get('password_animales','') or data.get('contraseña','')).strip()
        print(f"[LOGIN] Datos recibidos -> nombre='{nombre}' apellidos='{apellidos}' password='{password_animales}'")
        if not (nombre and apellidos and password_animales):
            raise web.seeother('/iniciar_sesion?error=campos')
        animales = [a for a in password_animales.split(',') if a]
        permitidos = {'ajolote','borrego','oso','perro'}
        if len(animales) != 6:
            raise web.seeother('/iniciar_sesion?error=pass')
        if any(a not in permitidos for a in animales):
            raise web.seeother('/iniciar_sesion?error=animales')
        try:
            conn = conectar_db(); cur = conn.cursor()
            cur.execute('''SELECT id_nino, nombres, apellidos, id_tutor, password_figuras FROM ninos
                           WHERE lower(nombres)=? AND lower(apellidos)=? AND password_figuras=? LIMIT 1''',
                        (nombre.lower(), apellidos.lower(), password_animales))
            row = cur.fetchone(); conn.close()
            print(f"[LOGIN] Resultado query -> {row}")
            if not row:
                raise web.seeother('/iniciar_sesion?error=credenciales')
            session.nino_id = row[0]
            session.user_type = 'nino'
            session.nino_nombre = row[1]
            session.nino_apellidos = row[2]
            session.tutor_id = row[3]
            print(f"✅ [LOGIN OK] Niño autenticado id={row[0]} nombre='{row[1]}'")
            raise web.seeother('/saludo_chiquillo')
        except web.HTTPError:
            raise
        except Exception as e:
            print('Error autenticando niño:', e)
            raise web.seeother('/iniciar_sesion?error=sistema')

class QuienesSomos:
    def GET(self):
        return render.quienes_somos()

class InicioAdministrador:
    def GET(self):
        return render.inicio_administrador()
    
    def POST(self):
        data = web.input()
        correo = data.get('correo', '').strip()
        password = data.get('contraseña', '')

        if not correo or not password:
            return "Error: Por favor ingresa tu correo y contraseña."

        # Aquí puedes agregar la lógica de autenticación
        # Por ahora, redirijo a perfil_admin para testing
        print(f"Intento de login: {correo}")
        raise web.seeother('/perfil_admin')

class SaludoChiquillo:
    def GET(self):
        return render.saludo_chiquillo()

class PresentacionLucas:
    def GET(self):
        return render.presentacion_lucas()

class PresentacionPagina:
    def GET(self):
        return render.presentacion_pagina()

class Lecciones:
    def GET(self):
        return render.lecciones()

class EditarPerfil:
    def GET(self):
        return render.editar_perfil()

class Introduccion:
    def GET(self):
        html_path = os.path.join(TEMPLATES_DIR, 'introduccion.html')
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "<h1>No se encontró la introducción</h1>"

class LeccionCoordinacion:
    def GET(self):
        return render.leccion_coordinacion()

class LeccionCompletada:
    def GET(self):
        return render.leccion_completada()

class Favicon:
    def GET(self):
        web.header('Content-Type', 'image/x-icon')
        return b''

class StaticFiles:
    def GET(self, path):
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.exists(file_path):
            ext = os.path.splitext(path)[1].lower()
            mime_types = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.mp3': 'audio/mpeg'
            }
            web.header('Content-Type', mime_types.get(ext, 'application/octet-stream'))
            with open(file_path, 'rb') as f:
                return f.read()
        else:
            raise web.notfound()

# ---------------- APP ----------------
app = web.application(urls, globals())

# Configuración de sesiones (usar ruta absoluta y manejo robusto)
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)
try:
    session = web.session.Session(app, web.session.DiskStore(SESSIONS_DIR),
                                  initializer={'tutor_id': None, 'user_type': None})
except PermissionError as e:
    print(f" No se pudo inicializar la sesión por permisos: {e}")
    # Fallback a memoria (no persistente)
    from web.session import Session
    class DummyStore(dict):
        def __contains__(self, key):
            return dict.__contains__(self, key)
    session = Session(app, DummyStore(), initializer={'tutor_id': None, 'user_type': None})

# Helper seguro para obtener atributos de sesión sin romper la app
def get_session_attr(name, default=None):
    try:
        return getattr(session, name, default)
    except Exception as e:
        print(f" Error leyendo atributo de sesión '{name}': {e}")
        return default

application = app.wsgifunc()

'''
if __name__ == "__main__":
    try:
        from waitress import serve
        
        # Inicializar la base de datos
        try:
            init_db()
            print("Base de datos inicializada correctamente")
        except Exception as e:
            print(f"Error al inicializar BD: {e}")
        
        print(" Servidor corriendo en http://localhost:8080")
        # Configuración optimizada para reducir warnings
        serve(application, 
              listen="*:8080",
              threads=6,        # Más threads para manejar solicitudes
              channel_timeout=120,
              cleanup_interval=30,
              log_socket_errors=False)  # Reducir logs de errores menores
    except ImportError:
        print("Waitress no instalado, usando servidor simple.")
        app.run()
'''
if __name__ == "__main__":
    app.run()




