import web

urls = (
    '/', 'Index',
    '/registrarme', 'Registrarme',
    '/iniciar_sesion', 'IniciarSesion',
    '/quienes_somos', 'QuienesSomos'
)

render = web.template.render('templates', cache=False)

app = web.application(urls, globals())

class Index:
    def GET(self):
        # Headers más agresivos para evitar caché
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '0')
        web.header('Last-Modified', '')
        web.header('ETag', '')
        web.header('Vary', '*')
        return render.index()

class Registrarme:
    def GET(self):
        # Headers para evitar caché
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '0')
        web.header('Last-Modified', '')
        web.header('ETag', '')
        web.header('Vary', '*')
        return render.registrarme()

class IniciarSesion:
    def GET(self):
        # Headers para evitar caché
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '0')
        web.header('Last-Modified', '')
        web.header('ETag', '')
        web.header('Vary', '*')
        return render.iniciar_sesion()

class QuienesSomos:
    def GET(self):
        # Headers para evitar caché
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '0')
        web.header('Last-Modified', '')
        web.header('ETag', '')
        web.header('Vary', '*')
        return render.quienes_somos()

if __name__ == "__main__":
    app.run()