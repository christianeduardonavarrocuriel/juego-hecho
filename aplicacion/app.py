"""
Aplicación web.py servida con Waitress.

Notas:
- Para ejecutarla con Waitress desde la raíz del proyecto:
        waitress-serve --listen=*:8080 app:application
- Usamos ruta absoluta para las plantillas para que funcione sin importar desde dónde se ejecute.
"""

import os
import web
import sqlite3
import re

# Modo producción (mejor rendimiento)
web.config.debug = False

# ---------------- RUTAS ----------------
urls = (
    '/', 'Index',
    '/registrar_tutor', 'RegistrarTutor',
    '/registrar_chiquillo', 'RegistrarChiquillo',
    '/inicio_administrador', 'InicioAdministrador',
    '/iniciar_sesion_nino', 'IniciarSesionNino',
    '/saludo_admin', 'SaludoAdmin',
    '/saludo_chiquillo', 'SaludoChiquillo',
    '/presentacion_lucas', 'PresentacionLucas',
    '/presentacion_pagina', 'PresentacionPagina',
    '/lecciones', 'Lecciones',
    '/perfil_admin', 'PerfilAdmin',
    '/perfil_chiquillo', 'PerfilChiquillo',
    '/editar_perfil', 'EditarPerfil',
    '/iniciar_sesion', 'IniciarSesion',
    '/logout', 'Logout',
    '/quienes_somos', 'QuienesSomos',
    '/introduccion', 'Introduccion',
    '/leccion_coordinacion', 'LeccionCoordinacion',
    '/leccion_completada', 'LeccionCompletada',
    '/favicon.ico', 'Favicon',
    '/static/(.*)', 'StaticFiles',
)

def conectar_db():
    # Construir la ruta absoluta a la base de datos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'registro.db')
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    """Inicializar la base de datos creando las tablas si no existen"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Crear tabla tutores
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
    
    # Crear tabla ninos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ninos (
            id_nino INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tutor INTEGER NOT NULL,
            genero TEXT NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            password_figuras TEXT NOT NULL,
            FOREIGN KEY (id_tutor) REFERENCES tutores(id_tutor) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

# Inicializar la base de datos al cargar el módulo
init_db()


# ---------------- CONFIGURACIÓN ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Crear carpeta templates si no existe
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Crear archivo index.html si no existe
index_path = os.path.join(TEMPLATES_DIR, 'index.html')
if not os.path.exists(index_path):
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("<h1>Hola, peque 🐣</h1><p>Página principal funcionando ✅</p>")

# Motor de plantillas
render = web.template.render(TEMPLATES_DIR, cache=False)

# ---------------- CLASES ----------------
class Index:
    def GET(self):
        return render.index()

class RegistrarTutor:
    def GET(self):
        return render.registrar_tutor()

    def POST(self):
        data = web.input()
        
        # --- Validación de datos ---
        correo = data.get('correo_tutor', '').strip()
        password = data.get('contraseña', '')

        # 1. Validar contraseña
        if len(password) != 6:
            return "Error: La contraseña debe tener exactamente 6 caracteres."

        # 2. Validar formato de correo
        if correo != correo.lower() or ' ' in correo or '@' not in correo or '.' not in correo:
            return "Error: Formato de correo electrónico inválido."

        # 3. Validar dominio de correo
        dominios_permitidos = [
            'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'live.com', 
            'msn.com', 'icloud.com', 'protonmail.com', 'zoho.com', 'aol.com', 
            'mail.com', 'gmx.com', 'unam.mx', 'ipn.mx', 'itesm.mx', 'udg.mx', 
            'uanl.mx', 'uach.mx', 'uas.mx', 'uaslp.mx', 'uv.mx', 'buap.mx', 
            'uat.mx', 'ujat.mx', 'unach.mx', 'uacj.mx', 'uabc.mx', 'uson.mx', 
            'uady.mx', 'ugto.mx', 'uaem.mx', 'uamx.mx', 'utec.edu.mx', 
            'utectulancingo.edu.mx', 'edu.mx', 'estudiantes.unam.mx', 
            'alumno.ipn.mx', 'itesm.edu.mx', 'tec.mx', 'estudiante.unam.mx', 
            'gob.mx', 'sep.gob.mx', 'conacyt.mx', 'cinvestav.mx'
        ]
        dominio = correo.split('@')[1]
        if dominio not in dominios_permitidos:
            return "Error: Solo se aceptan correos de proveedores conocidos (Gmail, Outlook, etc.) o instituciones educativas mexicanas."

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Normalizar el rol
            rol = data.get('tipo_usuario', '').lower()
            if rol == 'padre/madre':
                rol_normalizado = 'Padre/Madre'
            elif rol == 'tutor':
                rol_normalizado = 'Tutor'
            elif rol == 'maestro':
                rol_normalizado = 'Maestro'
            else:
                rol_normalizado = data.get('tipo_usuario', '')
            
            # Insertar tutor
            cursor.execute('''
                INSERT INTO tutores (rol, nombres, apellidos, correo, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                rol_normalizado,
                data.get('nombre', ''),
                data.get('primer_apellido_y_segundo_apellido', ''),
                correo,
                password
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ Tutor registrado exitosamente: {correo}")
            raise web.seeother('/registrar_chiquillo')
            
        except sqlite3.IntegrityError as e:
            print(f"Error de integridad: {e}")
            return "Error: El correo electrónico ya está registrado."
        except sqlite3.Error as e:
            print(f"Error de base de datos: {e}")
            return "Error en la base de datos. Por favor, inténtalo de nuevo."
        except Exception as e:
            print(f"Error general: {e}")
            return "Ocurrió un error durante el registro. Por favor, inténtalo de nuevo."

class RegistrarChiquillo:
    def GET(self):
        return render.registrar_chiquillo()

    def POST(self):
        data = web.input(
            genero=[], 
            nombres=[], 
            apellidos=[], 
            password_figuras=[]
        )
        
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Obtener ID del último tutor registrado
            cursor.execute("SELECT id_tutor FROM tutores ORDER BY id_tutor DESC LIMIT 1")
            tutor_result = cursor.fetchone()
            
            if not tutor_result:
                conn.close()
                return "Error: No se encontró un tutor para asociar a los niños."
            
            id_tutor = tutor_result[0]
            print(f"🔍 Registrando niños para tutor ID: {id_tutor}")
            
            # Asegurarse de que los datos sean listas
            generos = data.genero if isinstance(data.genero, list) else [data.genero]
            nombres = data.nombres if isinstance(data.nombres, list) else [data.nombres]
            apellidos = data.apellidos if isinstance(data.apellidos, list) else [data.apellidos]
            passwords = data.password_figuras if isinstance(data.password_figuras, list) else [data.password_figuras]

            print(f"📊 Datos recibidos: {len(generos)} géneros, {len(nombres)} nombres, {len(apellidos)} apellidos, {len(passwords)} contraseñas")

            # Validar que todas las listas tengan la misma longitud
            if not (len(generos) == len(nombres) == len(apellidos) == len(passwords)):
                conn.close()
                return "Error: Los datos de los niños no coinciden en cantidad."

            # Validar que haya al menos un niño
            if len(nombres) == 0:
                conn.close()
                return "Error: Debe registrar al menos un niño."

            # Preparar los datos para la inserción
            ninos_a_insertar = []
            for i in range(len(nombres)):
                genero = (generos[i] or '').strip()
                nombre = (nombres[i] or '').strip()
                apellido = (apellidos[i] or '').strip()
                password = (passwords[i] or '').strip()
                
                # Validar género permitido
                if genero not in ['Ajolotito', 'Ajolotita']:
                    conn.close()
                    return f"Error: Género inválido '{genero}' para el niño {i + 1}. Debe ser 'Ajolotito' o 'Ajolotita'."
                
                # Validar que los campos no estén vacíos
                if not all([genero, nombre, apellido, password]):
                    conn.close()
                    return f"Error: Faltan datos para el niño {i + 1}. Todos los campos son obligatorios."
                
                ninos_a_insertar.append((id_tutor, genero, nombre, apellido, password))
                print(f"👶 Niño {i+1}: {nombre} {apellido} ({genero})")

            # Insertar todos los niños en una sola transacción
            cursor.executemany('''
                INSERT INTO ninos (id_tutor, genero, nombres, apellidos, password_figuras)
                VALUES (?, ?, ?, ?, ?)
            ''', ninos_a_insertar)
            
            conn.commit()
            conn.close()
            
            print(f"✅ {len(ninos_a_insertar)} niño(s) registrado(s) exitosamente")
            raise web.seeother('/saludo_admin')
                
        except sqlite3.Error as e:
            print(f"❌ Error de base de datos al registrar niños: {e}")
            if 'conn' in locals():
                conn.close()
            return "Error en la base de datos al registrar los niños."
        except web.HTTPError:
            # Re-raise redirect exceptions (esto es normal y esperado)
            raise
        except Exception as e:
            print(f"❌ Error general al registrar niños: {e}")
            if 'conn' in locals():
                conn.close()
            return "Ocurrió un error al registrar los niños. Por favor, inténtalo de nuevo."

class IniciarSesionNino:
    def GET(self):
        # Esta podría ser una página específica para login de niños
        # Por ahora redirijo a la misma página de login
        return render.iniciar_sesion()

    def POST(self):
        data = web.input()
        nombre = data.get('nombre_nino', '').strip()
        password_figuras = data.get('password_figuras', '').strip()

        if not nombre or not password_figuras:
            return "Error: Por favor ingresa tu nombre y contraseña de figuras."

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Buscar el niño por nombre y contraseña de figuras
            cursor.execute('''
                SELECT n.id_nino, n.genero, n.nombres, n.apellidos, n.id_tutor,
                       t.nombres as tutor_nombres, t.apellidos as tutor_apellidos
                FROM ninos n
                JOIN tutores t ON n.id_tutor = t.id_tutor
                WHERE n.nombres = ? AND n.password_figuras = ?
            ''', (nombre, password_figuras))
            
            nino = cursor.fetchone()
            conn.close()
            
            if nino:
                # Iniciar sesión - guardar id del niño en la sesión
                session.user_id = nino[0]  # id_nino
                session.user_type = 'nino'  # Indicar que es un niño
                raise web.seeother('/saludo_chiquillo')
            else:
                return "Error: Nombre o contraseña de figuras incorrectos."
                
        except Exception as e:
            print(f"Error durante el inicio de sesión del niño: {e}")
            return "Error durante el inicio de sesión."

class SaludoAdmin:
    def GET(self):
        return render.saludo_admin()

class PerfilAdmin:
    def GET(self):
        # Verificar que hay un usuario logueado y que es un tutor
        if not session.get('user_id') or session.get('user_type') != 'tutor':
            print("❌ Acceso denegado: sin sesión de tutor válida")
            return web.seeother('/iniciar_sesion')
        
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Verificar que el tutor existe en la base de datos
            cursor.execute('''
                SELECT id_tutor, rol, nombres, apellidos, correo 
                FROM tutores 
                WHERE id_tutor = ?
            ''', (session.user_id,))
            
            tutor_data = cursor.fetchone()
            
            if not tutor_data:
                print(f"❌ Tutor no encontrado en BD: ID {session.user_id}")
                conn.close()
                # Limpiar sesión inválida
                session.kill()
                return web.seeother('/iniciar_sesion')
            
            print(f"✅ Tutor autenticado: {tutor_data[2]} {tutor_data[3]} ({tutor_data[4]})")
            
            # Convertir a diccionario para facilitar el acceso en la plantilla
            tutor = {
                'id_tutor': tutor_data[0],
                'rol': tutor_data[1],
                'nombres': tutor_data[2],
                'apellidos': tutor_data[3],
                'correo': tutor_data[4]
            }
            
            # Obtener niños asociados al tutor
            cursor.execute('''
                SELECT id_nino, genero, nombres, apellidos, password_figuras
                FROM ninos 
                WHERE id_tutor = ?
                ORDER BY nombres
            ''', (session.user_id,))
            
            ninos_data = cursor.fetchall()
            
            # Convertir a lista de diccionarios
            ninos = []
            for nino_data in ninos_data:
                ninos.append({
                    'id_nino': nino_data[0],
                    'genero': nino_data[1],
                    'nombres': nino_data[2],
                    'apellidos': nino_data[3],
                    'password_figuras': nino_data[4]
                })
            
            print(f"✅ Cargados {len(ninos)} niño(s) para el tutor")
            conn.close()
            return render.perfil_admin(tutor, ninos)
            
        except Exception as e:
            print(f"❌ Error al cargar el perfil: {e}")
            if 'conn' in locals():
                conn.close()
            return "Error al cargar el perfil del administrador."

class PerfilChiquillo:
    def GET(self):
        return render.perfil_chiquillo()

class IniciarSesion:
    def GET(self):
        return render.iniciar_sesion()

    def POST(self):
        data = web.input()
        correo = data.get('correo_tutor', '').strip()
        password = data.get('contraseña', '')

        if not correo or not password:
            return "Error: Por favor ingresa tu correo y contraseña."

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Buscar el tutor por correo y contraseña
            cursor.execute('''
                SELECT id_tutor, nombres, apellidos, correo 
                FROM tutores 
                WHERE correo = ? AND password = ?
            ''', (correo, password))
            
            tutor = cursor.fetchone()
            conn.close()
            
            if tutor:
                # Establecer sesión completa del tutor
                session.user_id = tutor[0]  # id_tutor
                session.user_type = 'tutor'  # Tipo de usuario
                session.user_name = f"{tutor[1]} {tutor[2]}"  # Nombre completo
                
                print(f"✅ Tutor autenticado exitosamente: {session.user_name} (ID: {tutor[0]})")
                print(f"✅ Sesión establecida con tipo: {session.user_type}")
                
                # Usar return en lugar de raise para evitar la captura como excepción
                return web.seeother('/perfil_admin')
            else:
                print(f"❌ Credenciales inválidas para correo: {correo}")
                return "Error: Correo o contraseña incorrectos."
                
        except Exception as e:
            print(f"❌ Error durante el inicio de sesión del administrador: {e}")
            return "Error durante el inicio de sesión."

class Logout:
    def GET(self):
        # Cerrar sesión
        session.kill()
        raise web.seeother('/')

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

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            
            # Buscar el tutor por correo y contraseña
            cursor.execute('''
                SELECT id_tutor, nombres, apellidos, correo, rol 
                FROM tutores 
                WHERE correo = ? AND password = ?
            ''', (correo, password))
            
            tutor = cursor.fetchone()
            conn.close()
            
            if tutor:
                # Iniciar sesión - guardar id del tutor en la sesión
                session.user_id = tutor[0]  # id_tutor
                raise web.seeother('/perfil_admin')
            else:
                return "Error: Correo o contraseña incorrectos."
                
        except Exception as e:
            print(f"Error durante el inicio de sesión del administrador: {e}")
            return "Error durante el inicio de sesión."

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

# Configurar sesiones después de crear la aplicación
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')

# Limpiar y recrear directorio de sesiones para evitar problemas de permisos
import shutil
if os.path.exists(SESSIONS_DIR):
    try:
        shutil.rmtree(SESSIONS_DIR)
    except:
        pass
os.makedirs(SESSIONS_DIR, exist_ok=True)

web.config.debug = False
session = web.session.Session(app, web.session.DiskStore(SESSIONS_DIR), initializer={'user_id': None, 'user_type': None})

application = app.wsgifunc()

if __name__ == "__main__":
    try:
        from waitress import serve
        print("🚀 Servidor corriendo en http://localhost:8080")
        serve(application, listen="*:8080")
    except ImportError:
        print("⚠️ Waitress no instalado, usando servidor simple.")
        app.run()