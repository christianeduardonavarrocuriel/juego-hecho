"""
Aplicación web.py para el juego educativo de ajolotes.
Sistema de registro de tutores y niños con autenticación por figuras.
"""

# IMPORTACIONES Y CONFIGURACIÓN INICIAL

# Importar librerías que necesitamos
import os           # Para trabajar con carpetas y archivos
import web          # Para crear páginas web
import sqlite3      # Para guardar datos en una base de datos

# Configurar rutas de carpetas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Carpeta donde está este archivo
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')    # Carpeta con las páginas HTML
STATIC_DIR = os.path.join(BASE_DIR, 'static')          # Carpeta con imágenes y sonidos

# Configurar cómo mostrar las páginas HTML
render = web.template.render(TEMPLATES_DIR, cache=False)  # Sin guardar en memoria

# FUNCIONES AUXILIARES DE BASE DE DATOS
def conectar_db():
    """
    Esta función se conecta a la base de datos donde guardamos la información
    """
    try:
        db_path = os.path.join(BASE_DIR, 'registro.db')  # Crear la ruta del archivo de base de datos
        
        # Si no existe la carpeta, crearla
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR, exist_ok=True)  # Crear carpeta
            
        conn = sqlite3.connect(db_path, timeout=10.0)    # Conectarse a la base de datos (esperar máximo 10 segundos)
        conn.execute('PRAGMA foreign_keys = ON;')        # Activar conexiones entre tablas
        conn.execute('PRAGMA journal_mode = WAL;')       # Modo especial para que varios usuarios puedan usar la base de datos
        return conn  # Devolver la conexión
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")  # Mostrar el error
        raise  # Parar el programa si no se puede conectar

def init_db():
    """
    Esta función crea las tablas en la base de datos donde guardamos la información
    """
    conn = conectar_db()        # Conectarse a la base de datos
    cursor = conn.cursor()      # Crear un "cursor" para escribir comandos en la base de datos
    
    # Crear tabla donde guardamos información de papás/tutores/maestros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tutores (
            id_tutor INTEGER PRIMARY KEY AUTOINCREMENT,  -- Número único para cada tutor (se genera automáticamente)
            rol TEXT NOT NULL,                           -- Si es Padre, Tutor o Maestro
            nombres TEXT NOT NULL,                       -- Nombres de la persona
            apellidos TEXT NOT NULL,                     -- Apellidos de la persona
            correo TEXT NOT NULL UNIQUE,                 -- Email (no puede repetirse)
            password TEXT NOT NULL                       -- Contraseña de 6 caracteres
        )
    ''')
    
    # Crear tabla donde guardamos información de los niños
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ninos (
            id_nino INTEGER PRIMARY KEY AUTOINCREMENT,   -- Número único para cada niño (se genera automáticamente)
            id_tutor INTEGER NOT NULL,                   -- Número del tutor que cuida a este niño
            genero TEXT NOT NULL CHECK(genero IN ('Ajolotito','Ajolotita')),  -- Solo puede ser Ajolotito o Ajolotita
            nombres TEXT NOT NULL,                       -- Nombres del niño
            apellidos TEXT NOT NULL,                     -- Apellidos del niño
            password_figuras TEXT NOT NULL,              -- Contraseña con 4 animales (ajolote,borrego,oso,perro)
            FOREIGN KEY (id_tutor) REFERENCES tutores(id_tutor) ON DELETE CASCADE  -- Conectar con la tabla de tutores
        )
    ''')
    
    conn.commit()  # Guardar los cambios en la base de datos
    conn.close()   # Cerrar la conexión
    print("Base de datos inicializada correctamente")

# FUNCIONES AUXILIARES DE SESIÓN
def set_nino_session(row):
    """
    Guarda la información del niño cuando se conecta al juego
    row = información del niño (id, nombre, apellidos, tutor, contraseña)
    """
    try:
        # Verificar si tenemos donde guardar la información de sesión
        if 'session' not in globals() or session is None:
            print(f"[SESION] No hay lugar para guardar la sesión")
            return False
            
        print(f"[SESION] === GUARDANDO INFORMACIÓN DEL NIÑO ===")
        print(f"[SESION] Información recibida: {row}")
        
        # Guardar información del niño en la sesión
        session.nino_id = row[0]        # Número único del niño
        session.nino_nombre = row[1]    # Nombre del niño
        session.nino_apellidos = row[2] # Apellidos del niño
        session.tutor_id = row[3]       # Número del tutor que lo cuida
        session.user_type = 'nino'      # Tipo de usuario = niño
        session.nino_activo = True      # El niño está conectado
        
        print(f"[SESION] Información guardada correctamente")
        return True
        
    except Exception as e:
        print(f"[SESION] Error guardando información: {e}")
        print(f"[SESION] Continuando sin guardar la sesión")
        return False

def limpiar_nino_session():
    """
    Borra la información del niño cuando sale del juego (cerrar sesión)
    """
    try:
        # Verificar si tenemos información guardada
        if 'session' not in globals() or session is None:
            return False
        
        # Ver si había un niño conectado antes de borrar
        had = bool(getattr(session, 'nino_activo', False) or getattr(session,'nino_id',None))
        
        # Desconectar al niño
        session.nino_activo = False
        
        # Borrar toda la información del niño
        for attr in ['nino_id','nino_nombre','nino_apellidos']:
            if hasattr(session, attr):
                setattr(session, attr, None)  # Poner en None = vacío
        
        # Si el tipo de usuario era niño, borrarlo también
        if getattr(session,'user_type',None)=='nino':
            session.user_type = None
            
        return had  # Devolver si había un niño conectado
        
    except Exception as e:
        print(f'[SESION] Error borrando información del niño: {e}')
        return False

def nino_sesion_activa():
    """
    Revisar si hay un niño conectado al juego en este momento
    """
    try:
        # Verificar si tenemos lugar donde guardar información de sesión
        if 'session' not in globals() or session is None:
            return False
        
        # Ver si hay un niño activo o con información guardada
        return bool(getattr(session,'nino_activo',False) or getattr(session,'nino_id',None))
    except Exception as e:
        print(f"Error verificando si hay niño conectado: {e}")
        return False

def get_session_attr(name, default=None):
    """
    Obtener información guardada de la sesión de forma segura
    """
    try:
        # Verificar si tenemos donde guardar información de sesión
        if 'session' in globals() and session is not None:
            return getattr(session, name, default)  # Buscar la información
        else:
            return default  # Si no hay sesión, devolver valor por defecto
    except Exception as e:
        print(f"Error obteniendo información de sesión '{name}': {e}")
        return default

# CONTROLADORES DE PÁGINAS WEB
class Index:
    """Esta clase maneja la página principal del juego"""
    def GET(self):
        """Cuando alguien visita la página principal"""
        # Revisar si hay un niño conectado
        activa = nino_sesion_activa()
        print(f"[INDEX] ¿Hay niño conectado? = {activa}")
        
        # Buscar el archivo de la página principal
        html_path = os.path.join(TEMPLATES_DIR, 'index.html')
        if os.path.exists(html_path):  # Si existe el archivo
            with open(html_path, 'r', encoding='utf-8') as f:
                contenido = f.read()  # Leer todo el contenido del archivo
                
            # Si hay un niño conectado, mostrar botón de salir
            if activa:
                # Código HTML para el botón de salir
                salir_html = ("<img src=\"/static/images/images_index/salir.png\" "
                              "alt=\"Salir\" style=\"width:70px;height:70px;cursor:pointer;\" "
                              "onclick=\"window.location.href='/cerrar_sesion'\">")
                contenido = contenido.replace('<!--LOGOUT_MARK-->', salir_html)  # Poner el botón en su lugar
                print(f"[INDEX] Mostrando botón salir para niño id={get_session_attr('nino_id')}")
            else:
                # Sin niño conectado, no mostrar botón
                contenido = contenido.replace('<!--LOGOUT_MARK-->', '')
                print(f"[INDEX] Sin niño conectado - no mostrar botón salir")
            return contenido
        return 'No se encontró la página principal'  # Error si no hay archivo

class CerrarSesion:
    """Esta clase maneja cuando un usuario quiere salir del juego"""
    def GET(self):
        """Cuando alguien hace clic en 'Salir'"""
        # Ver si había un niño conectado antes de desconectarlo
        activo = nino_sesion_activa()
        print(f"[LOGOUT] Estado antes: niño conectado={activo} id={get_session_attr('nino_id')} nombre={get_session_attr('nino_nombre')}")
        
        # Desconectar al niño y borrar su información
        had = limpiar_nino_session()
        print(f"[LOGOUT] Resultado -> se desconectó={had} ahora conectado={nino_sesion_activa()}")
        
        # Enviar al usuario de vuelta a la página principal
        raise web.seeother('/')

class RegistrarTutor:
    """Esta clase maneja el registro de papás, tutores y maestros"""
    def GET(self):
        """Mostrar la página para registrar un tutor"""
        return render.registrar_tutor()  # Mostrar el formulario HTML

    def POST(self):
        """Cuando alguien llena el formulario y lo envía"""
        data = web.input()  # Recibir la información del formulario
        print("Información del tutor recibida:", dict(data))
        
        # Limpiar la información recibida (quitar espacios extra)
        nombres = data.get('nombres','').strip()        # Nombres sin espacios
        apellidos = data.get('apellidos','').strip()    # Apellidos sin espacios
        correo = data.get('correo','').strip().lower()  # Email en minúsculas
        password = data.get('password','').strip()      # Contraseña
        rol = data.get('rol','').strip()                # Tipo de usuario (Padre/Tutor/Maestro)
        
        print(f"Información procesada -> nombres='{nombres}' apellidos='{apellidos}' correo='{correo}' password='{password}' rol='{rol}'")
        
        # Revisar que todos los campos estén llenos
        if not all([nombres, apellidos, correo, password, rol]):
            return "Error: Todos los campos son obligatorios."
        
        # La contraseña debe tener exactamente 6 caracteres
        if len(password) != 6:
            return "Error: La contraseña debe tener exactamente 6 caracteres."
        
        # El email debe tener @ y punto
        if '@' not in correo or '.' not in correo:
            return "Error: Formato de correo inválido."
        
        try:
            # Conectarse a la base de datos
            conn = conectar_db()
            cur = conn.cursor()
            
            # Arreglar el tipo de rol según lo que eligió el usuario
            if rol.lower() in ['padre','madre','padre/madre']:
                rol_normalizado = 'Padre'  # Todos los papás se guardan como "Padre"
            elif rol.lower()=='tutor':
                rol_normalizado='Tutor'
            elif rol.lower()=='maestro':
                rol_normalizado='Maestro'
            else:
                rol_normalizado='Padre'  # Si no reconocemos el rol, usar "Padre"
            
            # Guardar el nuevo tutor en la base de datos
            cur.execute('''INSERT INTO tutores (rol,nombres,apellidos,correo,password) VALUES (?,?,?,?,?)''',
                        (rol_normalizado,nombres,apellidos,correo,password))
            tutor_id = cur.lastrowid  # Obtener el número único que se le asignó al tutor
            conn.commit()  # Guardar los cambios
            conn.close()   # Cerrar conexión con la base de datos
            
            # Recordar el número del tutor para el siguiente paso
            session.tutor_id = tutor_id
            print(f"Tutor registrado exitosamente: {tutor_id} {nombres} {apellidos} {rol_normalizado}")
            
            # Llevar al usuario a la página para registrar niños
            raise web.seeother('/registrar_chiquillo')
            
        except sqlite3.IntegrityError:
            # Error: ya existe un tutor con ese email
            try: 
                conn.rollback()  # Cancelar los cambios
                conn.close()     # Cerrar conexión
            except Exception: 
                pass
            return "Error: El correo ya está registrado."
        except web.HTTPError:
            # Error de redirección (esto es normal, no hacer nada)
            raise
        except Exception as e:
            # Cualquier otro error
            try: 
                conn.rollback()  # Cancelar los cambios
                conn.close()     # Cerrar conexión
            except Exception: 
                pass
            print("Error registrando tutor:", e)
            return "Error al registrar el tutor."

class RegistrarChiquillo:
    """Controlador para el registro de niños"""
    def GET(self):
        """Mostrar formulario de registro de niño"""
        return render.registrar_chiquillo()  # Renderizar template

    def POST(self):
        """Procesar formulario de registro de niño"""
        data = web.input()  # Obtener datos del formulario
        print("Datos recibidos registrar_chiquillo:", dict(data))
        
        # Obtener ID del tutor de la sesión o fallback
        tutor_id = get_session_attr('tutor_id')
        if not tutor_id:
            try:
                # Fallback: obtener el último tutor registrado
                conn = conectar_db()
                cur = conn.cursor()
                cur.execute('SELECT MAX(id_tutor) FROM tutores')
                row = cur.fetchone()
                conn.close()
                tutor_id = row[0] if row and row[0] else None
                if tutor_id: 
                    session.tutor_id = tutor_id
            except Exception as e:
                print('Error fallback tutor:', e)
                return 'Error: Registre primero al tutor.'
                
        if not tutor_id:
            return 'Error: No hay tutor asociado.'
        
        # Buscar números en los nombres de los campos para saber cuántos niños hay
        indices = []
        for k in data.keys():  # Revisar todos los campos que llegaron
            if k.startswith('nombre_'):  # Si el campo empieza con "nombre_"
                try:
                    num = int(k.split('_')[1])  # Obtener el número después de "nombre_"
                    if num not in indices: 
                        indices.append(num)  # Agregar el número a la lista
                except ValueError: 
                    pass  # Si no es un número, ignorarlo
        indices.sort()  # Ordenar los números
        
        if not indices:
            return 'Error: No se recibieron niños.'
        
        # Animales permitidos para la contraseña visual
        permitidos = {'ajolote','borrego','oso','perro'}
        registros = []
        
        try:
            conn = conectar_db()
            cur = conn.cursor()
            
            # Procesar cada niño
            for idx in indices:
                nombre = data.get(f'nombre_{idx}','').strip()
                apellidos = data.get(f'apellidos_{idx}','').strip()
                genero = data.get(f'tipo_usuario_{idx}','').strip()
                password_raw = data.get(f'contraseña_{idx}','').strip()
                
                # Validaciones
                if not all([nombre, apellidos, genero, password_raw]):
                    return f'Error: Faltan datos en Niño {idx}.'
                if genero not in ['Ajolotito','Ajolotita']:
                    return f'Error: Género inválido en Niño {idx}.'
                
                # Separar los animales de la contraseña por comas
                animales = [a for a in password_raw.split(',') if a]  # Dividir por comas y quitar espacios vacíos
                if len(animales) != 4:  # Debe haber exactamente 4 animales
                    return f'Error: La contraseña del Niño {idx} debe tener exactamente 4 animales.'
                if any(a not in permitidos for a in animales):  # Todos los animales deben estar en la lista permitida
                    return f'Error: Niño {idx} tiene animales no permitidos.'
                
                password_figuras = ','.join(animales)  # Unir los animales con comas otra vez
                
                # Insertar niño en la base de datos
                cur.execute('''INSERT INTO ninos (id_tutor,genero,nombres,apellidos,password_figuras) VALUES (?,?,?,?,?)''',
                            (tutor_id, genero, nombre, apellidos, password_figuras))
                registros.append((cur.lastrowid, nombre))
            
            conn.commit()  # Confirmar todos los cambios
            conn.close()   # Cerrar conexión
            print('Niños insertados:', registros, 'Tutor', tutor_id)
            
            # Redireccionar al saludo del chiquillo
            raise web.seeother('/saludo_chiquillo')
            
        except web.HTTPError:
            raise
        except Exception as e:
            print('Error registrando niños:', e)
            try: 
                conn.rollback()
                conn.close()
            except Exception: 
                pass
            return 'Error al registrar los niños.'

class IniciarSesion:
    """Controlador para el inicio de sesión de niños"""
    def GET(self):
        """Mostrar formulario de inicio de sesión"""
        return render.iniciar_sesion()

    def POST(self):
        """Procesar autenticación de niño"""
        data = web.input()  # Obtener datos del formulario
        
        # Extraer campos del formulario
        nombre = data.get('nombre','').strip()
        apellidos = data.get('primer_apellido-y-segundo-apellido','').strip()
        password_animales = (data.get('password_animales','') or data.get('contraseña','')).strip()
        
        print(f"[LOGIN] Datos recibidos -> nombre='{nombre}' apellidos='{apellidos}' password='{password_animales}'")
        
        # Validación de campos
        if not (nombre and apellidos and password_animales):
            raise web.seeother('/iniciar_sesion?error=campos')
        
        # Validar formato de contraseña (debe ser 4 animales separados por comas)
        animales = [a for a in password_animales.split(',') if a]  # Separar por comas
        permitidos = {'ajolote','borrego','oso','perro'}  # Animales que se pueden usar
        
        if len(animales) != 4:  # Debe ser exactamente 4 animales
            raise web.seeother('/iniciar_sesion?error=pass')
        if any(a not in permitidos for a in animales):  # Todos deben estar en la lista permitida
            raise web.seeother('/iniciar_sesion?error=animales')
        
        try:
            # Buscar niño en la base de datos
            conn = conectar_db()
            cur = conn.cursor()
            cur.execute('''SELECT id_nino, nombres, apellidos, id_tutor, password_figuras FROM ninos
                           WHERE lower(nombres)=? AND lower(apellidos)=? AND password_figuras=? LIMIT 1''',
                        (nombre.lower(), apellidos.lower(), password_animales))
            row = cur.fetchone()
            conn.close()
            
            print(f"[LOGIN] Resultado query -> {row}")
            
            if not row:
                raise web.seeother('/iniciar_sesion?error=credenciales')
            
            # Establecer sesión del niño
            set_nino_session(row)
            print(f"[LOGIN OK] Niño autenticado id={row[0]} nombre='{row[1]}' sesion_activa={nino_sesion_activa()}")
            
            # Redirigir al saludo
            raise web.seeother('/saludo_chiquillo')
            
        except web.HTTPError:
            raise
        except Exception as e:
            print('Error autenticando niño:', e)
            raise web.seeother('/iniciar_sesion?error=sistema')

class InicioAdministrador:
    """Controlador para el inicio de sesión de administradores"""
    def GET(self):
        """Mostrar formulario de login de administrador"""
        return render.inicio_administrador()
    
    def POST(self):
        """Procesar autenticación de administrador"""
        data = web.input()
        correo = data.get('correo', '').strip().lower()
        password = data.get('contraseña', '').strip()

        print(f"[ADMIN-LOGIN] Intento de login -> correo='{correo}' password='{password}'")

        # Validaciones básicas
        if not correo or not password:
            print(f"[ADMIN-LOGIN] Campos vacíos")
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error: Por favor ingresa tu correo y contraseña.');</script>"

        if '@' not in correo or '.' not in correo:
            print(f"[ADMIN-LOGIN] Formato de correo inválido")
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error: Formato de correo inválido.');</script>"

        try:
            # Buscar tutor en la base de datos
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
                
                print(f"[ADMIN-LOGIN] Login exitoso - Tutor: {nombres} {apellidos} (ID: {tutor_id})")
                
                # Redirigir al perfil de administrador
                token = password[:3] + correo[:3]  # Token simple para backup
                raise web.seeother(f'/perfil_admin?tutor_id={tutor_id}&token={token}')
            else:
                # Credenciales incorrectas
                print(f"[ADMIN-LOGIN] Credenciales incorrectas para: {correo}")
                with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return html_content + "<script>alert('Error: Correo o contraseña incorrectos.');</script>"
                
        except web.HTTPError:
            raise
        except Exception as e:
            print(f"[ADMIN-LOGIN] Error en autenticación: {e}")
            with open(os.path.join(TEMPLATES_DIR, 'inicio_administrador.html'), 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content + "<script>alert('Error del sistema. Intenta de nuevo.');</script>"

class PerfilAdmin:
    """Controlador para el perfil de administrador"""
    def GET(self):
        """Mostrar perfil de administrador"""
        # Obtener parámetros de la URL (fallback si las sesiones no funcionan)
        input_data = web.input()
        url_tutor_id = input_data.get('tutor_id', None)
        url_token = input_data.get('token', None)
        
        # Verificar si hay sesión de administrador activa
        logged_in = get_session_attr('logged_in', False)
        session_tutor_id = get_session_attr('tutor_id', None)
        
        print(f"PerfilAdmin GET - logged_in: {logged_in}, session_tutor_id: {session_tutor_id}")
        print(f"URL params - tutor_id: {url_tutor_id}, token: {url_token}")
        
        # Determinar el tutor_id a usar (sesión o URL)
        tutor_id = session_tutor_id or url_tutor_id
        
        # Si no hay sesión activa ni parámetros válidos, redirigir al login
        if not tutor_id:
            print(f"Acceso denegado a perfil_admin - redirigiendo a inicio_administrador")
            raise web.seeother('/inicio_administrador')
        
        # Si viene de URL, validar el token
        if url_tutor_id and url_token:
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
                        print(f"Token válido para tutor {url_tutor_id}")
                        tutor_id = url_tutor_id
                        # Establecer sesión
                        try:
                            session.logged_in = True
                            session.tutor_id = int(url_tutor_id)
                            session.user_type = 'admin'
                            print(f"Sesión establecida desde URL params")
                        except Exception as session_error:
                            print(f"Error estableciendo sesión: {session_error}")
                    else:
                        print(f"Token inválido para tutor {url_tutor_id}")
                        raise web.seeother('/inicio_administrador')
                else:
                    print(f"Tutor no encontrado con ID: {url_tutor_id}")
                    raise web.seeother('/inicio_administrador')
            except Exception as e:
                print(f"Error validando token: {e}")
                raise web.seeother('/inicio_administrador')
        
        try:
            # Obtener datos del tutor desde la base de datos
            conn = conectar_db()
            cur = conn.cursor()
            
            tutor_id_int = int(tutor_id)
            
            cur.execute('''SELECT nombres, apellidos, correo, rol 
                           FROM tutores 
                           WHERE id_tutor = ?''', (tutor_id_int,))
            tutor_data = cur.fetchone()
            
            if not tutor_data:
                print(f"Tutor no encontrado con ID: {tutor_id_int}")
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
            
            print(f"Perfil admin cargado - Tutor: {tutor_info['nombres']} {tutor_info['apellidos']}, Niños: {len(ninos_info)}")
            
            return render.perfil_admin(tutor_info, ninos_info)
            
        except web.HTTPError:
            raise
        except Exception as e:
            print(f"Error cargando perfil admin: {e}")
            raise web.seeother('/inicio_administrador')

# Controladores simples para páginas estáticas
class SaludoAdmin:
    def GET(self):
        return render.saludo_admin()

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

class QuienesSomos:
    def GET(self):
        return render.quienes_somos()

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
    """Controlador para servir archivos estáticos (imágenes, CSS, JS, audio)"""
    def GET(self, path):
        """Servir archivo estático basado en la ruta solicitada"""
        file_path = os.path.join(STATIC_DIR, path)  # Construir ruta completa del archivo
        
        # Verificar si el archivo existe y es un archivo (no directorio)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            ext = os.path.splitext(path)[1].lower()  # Obtener extensión del archivo
            
            # Diccionario de tipos MIME para diferentes extensiones
            mime_types = {
                '.css': 'text/css',                    # Hojas de estilo CSS
                '.js': 'application/javascript',       # Archivos JavaScript
                '.png': 'image/png',                   # Imágenes PNG
                '.jpg': 'image/jpeg',                  # Imágenes JPEG
                '.jpeg': 'image/jpeg',                 # Imágenes JPEG (extensión completa)
                '.gif': 'image/gif',                   # Imágenes GIF
                '.mp3': 'audio/mpeg',                  # Archivos de audio MP3
                '.wav': 'audio/wav'                    # Archivos de audio WAV
            }
            
            # Establecer el tipo de contenido correcto en la cabecera HTTP
            web.header('Content-Type', mime_types.get(ext, 'application/octet-stream'))
            
            # Abrir y leer el archivo en modo binario
            with open(file_path, 'rb') as f:
                return f.read()  # Retornar contenido del archivo
        else:
            # Si el archivo no existe, retornar error 404
            raise web.notfound()

# CONFIGURACIÓN DE URLS Y APLICACIÓN
# Mapeo de rutas URL a clases controladoras
urls = (
    '/', 'Index',                                    # Página principal
    '/registrar_tutor', 'RegistrarTutor',           # Registro de tutores/padres
    '/registrar_chiquillo', 'RegistrarChiquillo',   # Registro de niños
    '/inicio_administrador', 'InicioAdministrador', # Login de administradores
    '/saludo_admin', 'SaludoAdmin',                 # Saludo para administradores
    '/saludo_chiquillo', 'SaludoChiquillo',         # Saludo para niños
    '/cerrar_sesion', 'CerrarSesion',               # Cerrar sesión
    '/presentacion_lucas', 'PresentacionLucas',     # Presentación del personaje Lucas
    '/presentacion_pagina', 'PresentacionPagina',   # Presentación de la página
    '/lecciones', 'Lecciones',                      # Página de lecciones
    '/perfil_admin', 'PerfilAdmin',                 # Perfil del administrador
    '/iniciar_sesion', 'IniciarSesion',             # Login de niños
    '/quienes_somos', 'QuienesSomos',               # Página "Quiénes Somos"
    '/introduccion', 'Introduccion',                # Lección de introducción
    '/leccion_coordinacion', 'LeccionCoordinacion', # Lección de coordinación
    '/leccion_completada', 'LeccionCompletada',     # Página de lección completada
    '/favicon.ico', 'Favicon',                      # Icono del sitio
    '/static/(.*)', 'StaticFiles',                  # Archivos estáticos
)

# Crear instancia de la aplicación web
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
    print(f"[SESION] Sesión inicializada correctamente con DiskStore")
except PermissionError as e:
    print(f"[SESION] No se pudo inicializar la sesión por permisos: {e}")
    # Fallback a memoria (no persistente)
    from web.session import Session
    class DummyStore(dict):
        def __contains__(self, key):
            return dict.__contains__(self, key)
    session = Session(app, DummyStore(), initializer=session_initializer)
    print(f"[SESION] Usando DummyStore (memoria) - sesiones no persistentes")

# PUNTO DE ENTRADA PRINCIPAL

# Crear función WSGI para deployment
application = app.wsgifunc()

if __name__ == "__main__":
    try:
        # Inicializar la base de datos al arrancar el servidor
        print("Inicializando base de datos...")
        init_db()
        print("Base de datos inicializada correctamente")
        
        # Configurar puerto del servidor
        PORT = 80
        HOST = '127.0.0.1'
        
        print(f"Servidor iniciando en http://{HOST}:{PORT}")
        print("Presiona Ctrl+C para detener el servidor")
        
        # Iniciar el servidor web
        import sys
        sys.argv = ['app.py', f'{HOST}:{PORT}']  # Configurar argumentos
        app.run()  # Iniciar el servidor
        
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")  # Cuando presionan Ctrl+C
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")
        print("Verifica que el puerto 8081 no esté en uso")
        import traceback
        traceback.print_exc()  # Mostrar detalles completos del error
