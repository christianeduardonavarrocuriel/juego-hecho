"""
Aplicación web.py simple para registro de usuarios.
"""

import os
import web
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

render = web.template.render(TEMPLATES_DIR, cache=False)

# URLs
urls = (
    '/', 'Index',
    '/registrar_tutor', 'RegistrarTutor',
    '/registrar_chiquillo', 'RegistrarChiquillo',
    '/static/(.*)', 'StaticFiles'
)

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'registro.db'))
    cursor = conn.cursor()
    
    # Tabla tutores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tutores (
            id_tutor INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT CHECK(rol IN ('Padre', 'Tutor', 'Maestro')) NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabla niños
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ninos (
            id_nino INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tutor INTEGER NOT NULL,
            genero TEXT CHECK(genero IN ('Ajolotito', 'Ajolotita')) NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            password_figuras TEXT NOT NULL,
            FOREIGN KEY (id_tutor) REFERENCES tutores(id_tutor)
        )
    ''')
    
    conn.commit()
    conn.close()

# Clases de las páginas
class Index:
    def GET(self):
        return render.index()

class RegistrarTutor:
    def GET(self):
        return render.registrar_tutor()
    
    def POST(self):
        data = web.input()
        try:
            conn = sqlite3.connect(os.path.join(BASE_DIR, 'registro.db'))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tutores (rol, nombres, apellidos, correo, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.rol,
                data.nombres,
                data.apellidos,
                data.correo,
                data.password
            ))
            
            conn.commit()
            conn.close()
            
            # Redirigir a página de éxito o index
            raise web.seeother('/')
            
        except sqlite3.IntegrityError:
            return render.registrar_tutor() + "<script>alert('El correo ya está registrado');</script>"
        except Exception as e:
            return render.registrar_tutor() + f"<script>alert('Error: {e}');</script>"

class RegistrarChiquillo:
    def GET(self):
        return render.registrar_chiquillo_simple()
    
    def POST(self):
        data = web.input()
        try:
            conn = sqlite3.connect(os.path.join(BASE_DIR, 'registro.db'))
            cursor = conn.cursor()
            
            # Buscar el tutor por correo
            cursor.execute('SELECT id_tutor FROM tutores WHERE correo = ?', (data.correo_tutor,))
            tutor = cursor.fetchone()
            
            if not tutor:
                return render.registrar_chiquillo() + "<script>alert('Tutor no encontrado');</script>"
            
            cursor.execute('''
                INSERT INTO ninos (nombres, apellidos, id_tutor, password_figuras, fecha_nacimiento)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.nombres,
                data.apellidos,
                tutor[0],
                data.password_figuras,
                data.fecha_nacimiento
            ))
            
            conn.commit()
            conn.close()
            
            # Redirigir a página de éxito o index
            raise web.seeother('/')
            
        except Exception as e:
            return render.registrar_chiquillo() + f"<script>alert('Error: {e}');</script>"

class StaticFiles:
    def GET(self, path):
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            ext = os.path.splitext(path)[1].lower()
            mime_types = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav'
            }
            web.header('Content-Type', mime_types.get(ext, 'application/octet-stream'))
            with open(file_path, 'rb') as f:
                return f.read()
        else:
            raise web.notfound()

# Aplicación
app = web.application(urls, globals())

if __name__ == "__main__":
    try:
        # Inicializar la base de datos
        init_db()
        print("✅ Base de datos inicializada correctamente")
        
        print("✅ Servidor corriendo en http://localhost:8080")
        
        # Intentar usar waitress
        try:
            from waitress import serve
            serve(app.wsgifunc(), host="127.0.0.1", port=8080)
        except ImportError:
            print("Waitress no instalado, usando servidor simple")
            import sys
            sys.argv = ['app.py', '127.0.0.1:8080']
            app.run()
            
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")

# -------- Helpers de sesión de niño (usarán la variable global session una vez inicializada) --------
def set_nino_session(row):
    """row: (id_nino, nombres, apellidos, id_tutor, password_figuras)"""
    global session
    try:
        print(f"[SESION] === ESTABLECIENDO SESIÓN NIÑO ===")
        print(f"[SESION] Datos recibidos: {row}")
        print(f"[SESION] Session object: {type(session)}")
        
        # Verificar si la sesión está inicializada
        try:
            session_id = session.session_id if hasattr(session, 'session_id') else 'No disponible'
            print(f"[SESION] Session ID antes: {session_id}")
        except:
            print(f"[SESION] Session ID antes: No accesible")
        
        # Asignar atributos de forma segura
        session.nino_id = row[0]
        session.nino_nombre = row[1]
        session.nino_apellidos = row[2]
        session.tutor_id = row[3]
        session.user_type = 'nino'
        session.nino_activo = True
        
        # Intentar múltiples métodos de guardado
        try:
            if hasattr(session, '_save'):
                session._save()
                print(f"[SESION] ✅ Sesión guardada con _save()")
            elif hasattr(session, 'flush'):
                session.flush()
                print(f"[SESION] ✅ Sesión guardada con flush()")
            else:
                print(f"[SESION] ⚠️ Sin método de guardado explícito disponible")
        except Exception as save_error:
            print(f"[SESION] ⚠️ Error en guardado explícito: {save_error}")
        
        # Verificar asignación
        attrs_after = {}
        for k in ['nino_id', 'nino_nombre', 'nino_apellidos', 'user_type', 'nino_activo']:
            try:
                attrs_after[k] = getattr(session, k, 'NO_ENCONTRADO')
            except:
                attrs_after[k] = 'ERROR_ACCESO'
        
        print(f"[SESION] Atributos después de asignar: {attrs_after}")
        
        try:
            session_id_after = session.session_id if hasattr(session, 'session_id') else 'No disponible'
            print(f"[SESION] Session ID después: {session_id_after}")
        except:
            print(f"[SESION] Session ID después: No accesible")
        
        print(f"[SESION] ✅ Configuración de sesión completada")
        
    except Exception as e:
        print(f"[SESION] ❌ Error estableciendo sesión: {e}")
        # No hacer raise para que el login pueda continuar
        print(f"[SESION] ⚠️ Continuando sin sesión persistente")

def limpiar_nino_session():
    global session
    if session is None:
        return False
    had = bool(getattr(session, 'nino_activo', False) or getattr(session,'nino_id',None))
    try:
        session.nino_activo = False
        for attr in ['nino_id','nino_nombre','nino_apellidos']:
            if hasattr(session, attr):
                setattr(session, attr, None)
        if getattr(session,'user_type',None)=='nino':
            session.user_type = None
    except Exception as e:
        print('[SESION] Error limpiando niño:', e)
    return had

def nino_sesion_activa():
    global session
    if session is None:
        return False
    return bool(getattr(session,'nino_activo',False) or getattr(session,'nino_id',None))

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
    '/cerrar_sesion', 'CerrarSesion',
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
    '/debug_ninos', 'DebugNinos',
    '/static/(.*)', 'StaticFiles',
)
class Index:
    def GET(self):
        # Diagnóstico completo de sesión
        print(f"[INDEX] === DIAGNÓSTICO DE SESIÓN ===")
        print(f"[INDEX] session object: {type(session)}")
        print(f"[INDEX] session_id: {getattr(session, 'session_id', 'N/A')}")
        try:
            attrs = {k: getattr(session, k, 'N/A') for k in ['nino_id', 'nino_nombre', 'nino_apellidos', 'user_type', 'nino_activo']}
            print(f"[INDEX] Atributos sesión: {attrs}")
        except Exception as e:
            print(f"[INDEX] Error leyendo sesión: {e}")
        
        activa = nino_sesion_activa()
        print(f"[INDEX] nino_sesion_activa() = {activa}")
        
        # Leemos plantilla base y si hay sesión de niño insertamos botón salir
        html_path = os.path.join(TEMPLATES_DIR, 'index.html')
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            if activa:
                salir_html = ("<img src=\"/static/images/images_index/salir.png\" "
                              "alt=\"Salir\" style=\"width:70px;height:70px;cursor:pointer;\" "
                              "onclick=\"window.location.href='/cerrar_sesion'\">")
                contenido = contenido.replace('<!--LOGOUT_MARK-->', salir_html)
                print(f"[INDEX] ✅ Mostrando botón salir para niño id={getattr(session,'nino_id',None)}")
            else:
                contenido = contenido.replace('<!--LOGOUT_MARK-->', '')
                print(f"[INDEX] ❌ Sin sesión activa - no mostrar botón salir")
            return contenido
        return 'Index no encontrado'

class CerrarSesion:
    def GET(self):
        activo = nino_sesion_activa()
        print(f"[LOGOUT-SOFT] Estado previo activo={activo} id={getattr(session,'nino_id',None)} nombre={getattr(session,'nino_nombre',None)}")
        had = limpiar_nino_session()
        print(f"[LOGOUT-SOFT] Resultado -> limpiado={had} ahora activo={nino_sesion_activa()}")
        raise web.seeother('/')

class RegistrarTutor:
    def GET(self):
        return render.registrar_tutor()

    def POST(self):
        data = web.input()
        print("Datos del tutor recibidos:", dict(data))
        # Usar los nombres correctos que vienen del formulario HTML
        nombres = data.get('nombres','').strip()
        apellidos = data.get('apellidos','').strip()
        correo = data.get('correo','').strip().lower()
        password = data.get('password','').strip()
        rol = data.get('rol','').strip()
        
        print(f"Campos procesados -> nombres='{nombres}' apellidos='{apellidos}' correo='{correo}' password='{password}' rol='{rol}'")
        
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
                if len(animales) != 4:
                    return f'Error: La contraseña del Niño {idx} debe tener exactamente 4 animales.'
                if any(a not in permitidos for a in animales):
                    return f'Error: Niño {idx} tiene animales no permitidos.'
                password_figuras = ','.join(animales)
                cur.execute('''INSERT INTO ninos (id_tutor,genero,nombres,apellidos,password_figuras) VALUES (?,?,?,?,?)''',
                            (tutor_id, genero, nombre, apellidos, password_figuras))
                registros.append((cur.lastrowid, nombre))
            conn.commit(); conn.close()
            print('✅ Niños insertados:', registros, 'Tutor', tutor_id)
            
            # Redireccionar directamente al saludo del chiquillo
            raise web.seeother('/saludo_chiquillo')
        except web.HTTPError:
            raise
        except Exception as e:
            print('❌ Error registrando niños:', e)
            try: conn.rollback(); conn.close()
            except Exception: pass
            return 'Error al registrar los niños.'

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
        # Obtener parámetros de la URL (fallback si las sesiones no funcionan)
        input_data = web.input()
        url_tutor_id = input_data.get('tutor_id', None)
        url_token = input_data.get('token', None)
        
        # Verificar si hay sesión de administrador activa
        logged_in = getattr(session, 'logged_in', False)
        session_tutor_id = getattr(session, 'tutor_id', None)
        
        print(f"🔍 PerfilAdmin GET - logged_in: {logged_in}, session_tutor_id: {session_tutor_id}")
        print(f"🔍 URL params - tutor_id: {url_tutor_id}, token: {url_token}")
        
        # Determinar el tutor_id a usar (sesión o URL)
        tutor_id = session_tutor_id or url_tutor_id
        
        # Si no hay sesión activa ni parámetros válidos, redirigir al login
        if not tutor_id:
            print(f"❌ Acceso denegado a perfil_admin - redirigiendo a inicio_administrador")
            raise web.seeother('/inicio_administrador')
        
        # Si viene de URL, validar el token
        if url_tutor_id and url_token:
            try:
                # Validar que el tutor existe y el token coincide
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT correo, password 
                               FROM tutores 
                               WHERE id_tutor = ?''', (url_tutor_id,))
                tutor_check = cur.fetchone()
                conn.close()
                
                if tutor_check:
                    correo, password = tutor_check
                    expected_token = password[:3] + correo[:3]
                    if url_token == expected_token:
                        print(f"✅ Token válido para tutor {url_tutor_id}")
                        tutor_id = url_tutor_id
                        # Establecer sesión ahora que sabemos que es válido
                        try:
                            session.logged_in = True
                            session.tutor_id = int(url_tutor_id)  # Asegurar que sea entero
                            session.user_type = 'admin'
                            print(f"💾 Sesión establecida desde URL params")
                        except Exception as session_error:
                            print(f"⚠️ Error estableciendo sesión: {session_error}")
                            # Continuar con tutor_id como string si hay problemas
                    else:
                        print(f"❌ Token inválido para tutor {url_tutor_id}")
                        raise web.seeother('/inicio_administrador')
                else:
                    print(f"❌ Tutor no encontrado con ID: {url_tutor_id}")
                    raise web.seeother('/inicio_administrador')
            except Exception as e:
                print(f"❌ Error validando token: {e}")
                raise web.seeother('/inicio_administrador')
        
        try:
            # Obtener datos del tutor desde la base de datos
            conn = conectar_db()
            cur = conn.cursor()
            
            # Asegurar que tutor_id sea entero para la consulta
            tutor_id_int = int(tutor_id)
            
            cur.execute('''SELECT nombres, apellidos, correo, rol 
                           FROM tutores 
                           WHERE id_tutor = ?''', (tutor_id_int,))
            tutor_data = cur.fetchone()
            
            if not tutor_data:
                print(f"❌ Tutor no encontrado con ID: {tutor_id_int}")
                raise web.seeother('/inicio_administrador')
            
            # Obtener niños asociados al tutor
            cur.execute('''SELECT nombres, apellidos, genero, password_figuras 
                           FROM ninos 
                           WHERE id_tutor = ? 
                           ORDER BY nombres''', (tutor_id_int,))
            ninos_data = cur.fetchall()
            
            conn.close()
            
            # Preparar datos para la plantilla
            tutor_info = {
                'nombres': tutor_data[0],
                'apellidos': tutor_data[1],
                'correo': tutor_data[2],
                'rol': tutor_data[3]
            }
            
            ninos_info = []
            for nino in ninos_data:
                ninos_info.append({
                    'nombres': nino[0],
                    'apellidos': nino[1],
                    'genero': nino[2],
                    'password_figuras': nino[3]
                })
            
            print(f"✅ Perfil admin cargado - Tutor: {tutor_info['nombres']} {tutor_info['apellidos']}, Niños: {len(ninos_info)}")
            
            return render.perfil_admin(tutor_info, ninos_info)
            
        except web.HTTPError:
            raise
        except Exception as e:
            print(f"❌ Error cargando perfil admin: {e}")
            raise web.seeother('/inicio_administrador')

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
        if len(animales) != 4:
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
            set_nino_session(row)
            print(f"✅ [LOGIN OK] Niño autenticado id={row[0]} nombre='{row[1]}' sesion_activa={nino_sesion_activa()}")
            
            # Diagnóstico post-login
            print(f"[LOGIN] === POST-LOGIN DIAGNÓSTICO ===")
            try:
                attrs = {k: getattr(session, k, 'N/A') for k in ['nino_id', 'nino_nombre', 'nino_apellidos', 'user_type', 'nino_activo']}
                print(f"[LOGIN] Atributos después de set_nino_session: {attrs}")
            except Exception as e:
                print(f"[LOGIN] Error leyendo sesión post-login: {e}")
            
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
        correo = data.get('correo', '').strip().lower()
        password = data.get('contraseña', '').strip()

        print(f"[ADMIN-LOGIN] Intento de login -> correo='{correo}' password='{password}'")

        # Validar que los campos no estén vacíos
        if not correo or not password:
            print(f"[ADMIN-LOGIN] ❌ Campos vacíos")
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error: Por favor ingresa tu correo y contraseña.');</script>"

        # Validar formato básico de correo
        if '@' not in correo or '.' not in correo:
            print(f"[ADMIN-LOGIN] ❌ Formato de correo inválido")
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error: Formato de correo inválido.');</script>"

        try:
            # Conectar a la base de datos y buscar el tutor
            conn = conectar_db()
            cur = conn.cursor()
            
            cur.execute('''SELECT id_tutor, nombres, apellidos, rol, correo, password 
                           FROM tutores 
                           WHERE lower(correo) = ? AND password = ? 
                           LIMIT 1''', (correo, password))
            
            tutor = cur.fetchone()
            conn.close()
            
            if tutor:
                # Usuario encontrado - crear sesión
                tutor_id, nombres, apellidos, rol, correo_db, password_db = tutor
                
                # Establecer sesión de administrador
                session.logged_in = True
                session.tutor_id = tutor_id
                session.user_type = 'admin'
                session.tutor_nombres = nombres
                session.tutor_apellidos = apellidos
                session.tutor_rol = rol
                session.tutor_correo = correo_db
                
                # Forzar guardado de sesión
                try:
                    # Intentar múltiples métodos para asegurar que la sesión se guarde
                    if hasattr(session, '_save'):
                        session._save()
                        print(f"💾 [ADMIN-LOGIN] Sesión guardada con _save()")
                    elif hasattr(session, 'save'):
                        session.save()
                        print(f"💾 [ADMIN-LOGIN] Sesión guardada con save()")
                    else:
                        # Forzar guardado asignando nuevamente un atributo
                        session.admin_login_time = 'logged_in'
                        print(f"💾 [ADMIN-LOGIN] Sesión forzada con timestamp")
                except Exception as save_error:
                    print(f"⚠️ [ADMIN-LOGIN] Error guardando sesión: {save_error}")
                    # Continuar aunque haya error en el guardado
                
                print(f"✅ [ADMIN-LOGIN] Login exitoso - Tutor: {nombres} {apellidos} (ID: {tutor_id}, Rol: {rol})")
                print(f"🔒 Sesión creada: logged_in=True, tutor_id={tutor_id}")
                
                # Verificación inmediata de sesión
                verificacion = getattr(session, 'logged_in', False)
                print(f"🔍 Verificación inmediata: {verificacion}")
                
                # Siempre usar redirección con token como backup
                # (las sesiones web.py a veces no persisten entre requests)
                print(f"🔄 [ADMIN-LOGIN] Usando redirección con token por seguridad")
                token = password[:3] + correo[:3]  # Token simple basado en credenciales
                raise web.seeother(f'/perfil_admin?tutor_id={tutor_id}&token={token}')
            else:
                # Usuario no encontrado o credenciales incorrectas
                print(f"❌ [ADMIN-LOGIN] Credenciales incorrectas para: {correo}")
                # Leer el HTML del template y agregar el script de alerta
                with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return html_content + "<script>alert('Error: Correo o contraseña incorrectos.');</script>"
                
        except web.HTTPError:
            raise
        except Exception as e:
            print(f"❌ [ADMIN-LOGIN] Error en autenticación: {e}")
            # Leer el HTML del template y agregar el script de alerta
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error del sistema. Intenta de nuevo.');</script>"

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
        # Verificar que hay sesión de administrador activa
        logged_in = getattr(session, 'logged_in', False)
        tutor_id = getattr(session, 'tutor_id', None)
        
        # También revisar parámetros URL como fallback
        input_data = web.input()
        url_tutor_id = input_data.get('tutor_id', None)
        url_token = input_data.get('token', None)
        
        if not tutor_id and url_tutor_id and url_token:
            # Validar token si viene de URL
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT correo, password FROM tutores WHERE id_tutor = ?''', (url_tutor_id,))
                tutor_check = cur.fetchone()
                conn.close()
                
                if tutor_check:
                    correo, password = tutor_check
                    expected_token = password[:3] + correo[:3]
                    if url_token == expected_token:
                        tutor_id = url_tutor_id
                        # Establecer sesión
                        session.logged_in = True
                        session.tutor_id = int(url_tutor_id)
                        session.user_type = 'admin'
            except Exception as e:
                print(f"Error validando token en editar_perfil: {e}")
        
        if not tutor_id:
            print(f"❌ Acceso denegado a editar_perfil - redirigiendo a inicio_administrador")
            raise web.seeother('/inicio_administrador')
        
        try:
            # Obtener datos actuales del tutor
            conn = conectar_db()
            cur = conn.cursor()
            cur.execute('''SELECT nombres, apellidos, correo, rol, password 
                           FROM tutores 
                           WHERE id_tutor = ?''', (int(tutor_id),))
            tutor_data = cur.fetchone()
            conn.close()
            
            if not tutor_data:
                raise web.seeother('/inicio_administrador')
            
            # Preparar datos para la plantilla
            tutor_info = {
                'nombres': tutor_data[0],
                'apellidos': tutor_data[1],
                'correo': tutor_data[2],
                'rol': tutor_data[3],
                'password': tutor_data[4]
            }
            
            return render.editar_perfil_nuevo(tutor_info)
            
        except Exception as e:
            print(f"❌ Error obteniendo datos del tutor para editar: {e}")
            raise web.seeother('/perfil_admin')
    
    def POST(self):
        print(f"[EDITAR_PERFIL] POST iniciado")
        
        # Verificar sesión de administrador
        logged_in = getattr(session, 'logged_in', False)
        tutor_id = getattr(session, 'tutor_id', None)
        
        print(f"[EDITAR_PERFIL] Estado sesión: logged_in={logged_in}, tutor_id={tutor_id}")
        
        # También revisar parámetros URL como fallback (igual que en GET)
        input_data = web.input()
        url_tutor_id = input_data.get('tutor_id', None)
        url_token = input_data.get('token', None)
        
        if not tutor_id and url_tutor_id and url_token:
            print(f"[EDITAR_PERFIL] Intentando validar token desde URL")
            # Validar token si viene de URL
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT correo, password FROM tutores WHERE id_tutor = ?''', (url_tutor_id,))
                tutor_check = cur.fetchone()
                conn.close()
                
                if tutor_check:
                    correo, password = tutor_check
                    expected_token = password[:3] + correo[:3]
                    if url_token == expected_token:
                        tutor_id = url_tutor_id
                        # Establecer sesión
                        session.logged_in = True
                        session.tutor_id = int(url_tutor_id)
                        session.user_type = 'admin'
                        print(f"✅ [EDITAR_PERFIL] Token válido, sesión establecida para tutor {tutor_id}")
            except Exception as e:
                print(f"❌ [EDITAR_PERFIL] Error validando token: {e}")
        
        if not tutor_id:
            print(f"[EDITAR_PERFIL] ❌ Sin sesión válida - redirigiendo a login")
            raise web.seeother('/inicio_administrador')
        
        data = web.input()
        nombres = data.get('nombres', '').strip()
        apellidos = data.get('apellidos', '').strip()
        correo = data.get('correo', '').strip().lower()
        rol = data.get('rol', '').strip()
        password = data.get('password', '').strip()
        verificar_password = data.get('verificar_password', '').strip()
        
        print(f"[EDITAR_PERFIL] Datos recibidos - nombres: {nombres}, apellidos: {apellidos}, correo: {correo}, rol: {rol}, password: {password}")
        
        # Validaciones
        if not all([nombres, apellidos, correo, rol, password]):
            # Recargar página con error
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT nombres, apellidos, correo, rol, password FROM tutores WHERE id_tutor = ?''', (int(tutor_id),))
                tutor_data = cur.fetchone()
                conn.close()
                tutor_info = {
                    'nombres': tutor_data[0], 'apellidos': tutor_data[1], 'correo': tutor_data[2], 
                    'rol': tutor_data[3], 'password': tutor_data[4]
                }
                return render.editar_perfil_nuevo(tutor_info) + "<script>alert('Error: Todos los campos son obligatorios.');</script>"
            except Exception:
                raise web.seeother('/perfil_admin')
        
        if len(password) != 6:
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT nombres, apellidos, correo, rol, password FROM tutores WHERE id_tutor = ?''', (int(tutor_id),))
                tutor_data = cur.fetchone()
                conn.close()
                tutor_info = {
                    'nombres': tutor_data[0], 'apellidos': tutor_data[1], 'correo': tutor_data[2], 
                    'rol': tutor_data[3], 'password': tutor_data[4]
                }
                return render.editar_perfil_nuevo(tutor_info) + "<script>alert('Error: La contraseña debe tener exactamente 6 caracteres.');</script>"
            except Exception:
                raise web.seeother('/perfil_admin')
        
        if password != verificar_password:
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT nombres, apellidos, correo, rol, password FROM tutores WHERE id_tutor = ?''', (int(tutor_id),))
                tutor_data = cur.fetchone()
                conn.close()
                tutor_info = {
                    'nombres': tutor_data[0], 'apellidos': tutor_data[1], 'correo': tutor_data[2], 
                    'rol': tutor_data[3], 'password': tutor_data[4]
                }
                return render.editar_perfil_nuevo(tutor_info) + "<script>alert('Error: Las contraseñas no coinciden.');</script>"
            except Exception:
                raise web.seeother('/perfil_admin')
        
        if '@' not in correo or '.' not in correo:
            try:
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT nombres, apellidos, correo, rol, password FROM tutores WHERE id_tutor = ?''', (int(tutor_id),))
                tutor_data = cur.fetchone()
                conn.close()
                tutor_info = {
                    'nombres': tutor_data[0], 'apellidos': tutor_data[1], 'correo': tutor_data[2], 
                    'rol': tutor_data[3], 'password': tutor_data[4]
                }
                return render.editar_perfil_nuevo(tutor_info) + "<script>alert('Error: Formato de correo inválido.');</script>"
            except Exception:
                raise web.seeother('/perfil_admin')
        
        # Normalizar rol
        if rol.lower() in ['padre','madre','padre/madre']:
            rol_normalizado = 'Padre'
        elif rol.lower() == 'tutor':
            rol_normalizado = 'Tutor'
        elif rol.lower() == 'maestro':
            rol_normalizado = 'Maestro'
        else:
            rol_normalizado = 'Padre'
        
        try:
            # Actualizar datos en la base de datos
            conn = conectar_db()
            cur = conn.cursor()
            
            # Verificar si el correo ya existe en otro tutor
            cur.execute('''SELECT id_tutor FROM tutores WHERE correo = ? AND id_tutor != ?''', (correo, int(tutor_id)))
            existing_tutor = cur.fetchone()
            
            if existing_tutor:
                conn.close()
                # Recargar con datos actuales y mostrar error
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('''SELECT nombres, apellidos, correo, rol, password FROM tutores WHERE id_tutor = ?''', (int(tutor_id),))
                tutor_data = cur.fetchone()
                conn.close()
                tutor_info = {
                    'nombres': tutor_data[0], 'apellidos': tutor_data[1], 'correo': tutor_data[2], 
                    'rol': tutor_data[3], 'password': tutor_data[4]
                }
                return render.editar_perfil_nuevo(tutor_info) + "<script>alert('Error: El correo ya está registrado por otro usuario.');</script>"
            
            # Actualizar el tutor
            cur.execute('''UPDATE tutores 
                          SET nombres = ?, apellidos = ?, correo = ?, rol = ?, password = ?
                          WHERE id_tutor = ?''', 
                          (nombres, apellidos, correo, rol_normalizado, password, int(tutor_id)))
            
            conn.commit()
            conn.close()
            
            # Actualizar datos de sesión
            session.tutor_nombres = nombres
            session.tutor_apellidos = apellidos
            session.tutor_correo = correo
            session.tutor_rol = rol_normalizado
            
            print(f"✅ Perfil actualizado exitosamente para tutor {tutor_id}: {nombres} {apellidos}")
            
            # Redirigir de vuelta al perfil con mensaje de éxito
            raise web.seeother('/perfil_admin?updated=1')
            
        except web.HTTPError:
            raise
        except Exception as e:
            print(f"❌ Error actualizando perfil: {e}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            raise web.seeother('/perfil_admin')

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
print(f"[SESION] Directorio de sesiones: {SESSIONS_DIR}")

# Initializer completo con todos los atributos necesarios
session_initializer = {
    'tutor_id': None, 
    'user_type': None,
    'nino_id': None,
    'nino_nombre': None,
    'nino_apellidos': None,
    'nino_activo': False,
    # Atributos para administrador
    'logged_in': False,
    'tutor_nombres': None,
    'tutor_apellidos': None,
    'tutor_rol': None,
    'tutor_correo': None
}

try:
    session = web.session.Session(app, web.session.DiskStore(SESSIONS_DIR),
                                  initializer=session_initializer)
    print(f"[SESION] ✅ Sesión inicializada correctamente con DiskStore")
except PermissionError as e:
    print(f"[SESION] ❌ No se pudo inicializar la sesión por permisos: {e}")
    # Fallback a memoria (no persistente)
    from web.session import Session
    class DummyStore(dict):
        def __contains__(self, key):
            return dict.__contains__(self, key)
    session = Session(app, DummyStore(), initializer=session_initializer)
    print(f"[SESION] ⚠️ Usando DummyStore (memoria) - sesiones no persistentes")

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
    import sys
    sys.argv = ['app.py', '127.0.0.1:8081']
    app.run()
