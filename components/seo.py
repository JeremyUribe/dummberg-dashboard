"""Rutas SEO de Bondora."""

from flask import Response


def register_seo_routes(server):
    """Registra las rutas SEO en el servidor Flask de Dash."""

    @server.route("/robots.txt")
    def robots_txt():
        contenido = (
            "User-agent: *\n"
            "Disallow:\n"
            "\n"
            "Sitemap: https://bondora.onrender.com/sitemap.xml\n"
        )
        return Response(contenido, mimetype="text/plain")

    @server.route("/sitemap.xml")
    def sitemap_xml():
        contenido = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://bondora.onrender.com/</loc>
    </url>
</urlset>"""
        return Response(contenido, mimetype="application/xml")
