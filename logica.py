# -*- coding: utf-8 -*-
"""
logica.py  -  Núcleo de CifraApp
================================
Busca una canción en Cifra Club y genera un PDF con acordes, letra y diagramas.

Este archivo NO sabe que existe una ventana. No importa tkinter, no importa
kivy, no importa android. Recibe texto, devuelve un archivo.
Funciona igual en Windows, Linux y Android.
"""

import os
import re
import unicodedata
import urllib.parse

from bs4 import BeautifulSoup

# --- Backend HTTP ---------------------------------------------------------
IMPERSONAR = False
try:
    from curl_cffi import requests as _http
    IMPERSONAR = True
    import requests
except ImportError:
    import requests as _http
    import requests

requests = _http
BACKEND = "curl_cffi (impersonate chrome120)" if IMPERSONAR else "requests (sin impersonate)"

try:
    import curl_cffi as _cc
    VERSION_HTTP = _cc.__version__
except Exception:
    VERSION_HTTP = getattr(_http, "__version__", "?")

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle, Frame, FrameBreak, PageTemplate)
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from reportlab.pdfgen import canvas

BASE = "https://www.cifraclub.com.br"
TIMEOUT = 20

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Mobile Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,es;q=0.8,en;q=0.7",
}

HEADERS_ESCRITORIO = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,es;q=0.8,en;q=0.7",
}

INVISIBLES = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u00a0"), None)

# ---------------------------------------------------------------------------
# DICCIONARIO DE ACORDES
# ---------------------------------------------------------------------------
DIC_ACORDES = {
    'C': [-1, 3, 2, 0, 1, 0], 'C#': [-1, 4, 6, 6, 6, 4], 'Db': [-1, 4, 6, 6, 6, 4],
    'D': [-1, -1, 0, 2, 3, 2], 'D#': [-1, 6, 8, 8, 8, 6], 'Eb': [-1, 6, 8, 8, 8, 6],
    'E': [0, 2, 2, 1, 0, 0], 'F': [1, 3, 3, 2, 1, 1], 'F#': [2, 4, 4, 3, 2, 2],
    'Gb': [2, 4, 4, 3, 2, 2], 'G': [3, 2, 0, 0, 0, 3], 'G#': [4, 6, 6, 5, 4, 4],
    'Ab': [4, 6, 6, 5, 4, 4], 'A': [-1, 0, 2, 2, 2, 0], 'A#': [-1, 1, 3, 3, 3, 1],
    'Bb': [-1, 1, 3, 3, 3, 1], 'B': [-1, 2, 4, 4, 4, 2],
    'Cm': [-1, 3, 5, 5, 4, 3], 'C#m': [-1, 4, 6, 6, 5, 4], 'Dm': [-1, -1, 0, 2, 3, 1],
    'D#m': [-1, 6, 8, 8, 7, 6], 'Ebm': [-1, 6, 8, 8, 7, 6], 'Em': [0, 2, 2, 0, 0, 0],
    'Fm': [1, 3, 3, 1, 1, 1], 'F#m': [2, 4, 4, 2, 2, 2], 'Gm': [3, 5, 5, 3, 3, 3],
    'G#m': [4, 6, 6, 4, 4, 4], 'Abm': [4, 6, 6, 4, 4, 4], 'Am': [-1, 0, 2, 2, 1, 0],
    'A#m': [-1, 1, 3, 3, 2, 1], 'Bbm': [-1, 1, 3, 3, 2, 1], 'Bm': [-1, 2, 4, 4, 3, 2],
    'C7': [-1, 3, 2, 3, 1, 0], 'D7': [-1, -1, 0, 2, 1, 2], 'E7': [0, 2, 0, 1, 0, 0],
    'F7': [1, 3, 1, 2, 1, 1], 'G7': [3, 2, 0, 0, 0, 1], 'A7': [-1, 0, 2, 0, 2, 0],
    'B7': [-1, 2, 1, 2, 0, 2],
    'Cm7': [-1, 3, 5, 3, 4, 3], 'Dm7': [-1, -1, 0, 2, 1, 1], 'Em7': [0, 2, 2, 0, 3, 0],
    'Fm7': [1, 3, 1, 1, 1, 1], 'Gm7': [3, 5, 3, 3, 3, 3], 'Am7': [-1, 0, 2, 0, 1, 0],
    'Bm7': [-1, 2, 4, 2, 3, 2],
    'Cmaj7': [-1, 3, 2, 0, 0, 0], 'Dmaj7': [-1, -1, 0, 2, 2, 2],
    'Emaj7': [0, 2, 1, 1, 0, 0], 'Fmaj7': [-1, -1, 3, 2, 1, 0],
    'Gmaj7': [3, 2, 0, 0, 0, 2], 'Amaj7': [-1, 0, 2, 1, 2, 0],
    'Bmaj7': [-1, 2, 4, 3, 4, 2],
    'Csus4': [-1, 3, 3, 0, 1, 1], 'Dsus4': [-1, -1, 0, 2, 3, 3],
    'Esus4': [0, 2, 2, 2, 0, 0], 'Gsus4': [3, 3, 0, 0, 1, 3],
    'Asus4': [-1, 0, 2, 2, 3, 0],
}

PATRON_ACORDE = re.compile(
    r'^[A-G][b#]?(m|maj|min|dim|aug|add|sus|º|°)?'
    r'([0-9]{1,2})?'
    r'(M|maj|m|°|º|\+|-)?'
    r'(\([^)]*\))?'
    r'(\/[A-G][b#]?)?$'
)

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------
def slugificar(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s-]', '', texto)
    return re.sub(r'[-\s]+', '-', texto).strip('-')

def limpiar_texto(texto):
    return texto.translate(INVISIBLES).replace('\r\n', '\n').replace('\r', '\n')

def carpeta_trabajo():
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            base = app.user_data_dir
            ruta = os.path.join(base, "acordes")
            os.makedirs(ruta, exist_ok=True)
            return ruta
    except Exception:
        pass

    ruta = os.path.join(os.path.expanduser("~"), "CifraApp", "acordes")
    try:
        os.makedirs(ruta, exist_ok=True)
    except Exception:
        ruta = os.path.expanduser("~")
    return ruta

LOG = []

def _log(msg):
    LOG.append(str(msg))
    return None

def _get(url, timeout=TIMEOUT, reintentar=True):
    extra = {"impersonate": "chrome120"} if IMPERSONAR else {}

    def _pedir(cabeceras):
        return _http.get(url, headers=cabeceras, timeout=timeout, **extra)

    try:
        r = _pedir(HEADERS)
        _log("GET %s -> HTTP %s (%s bytes)" % (url, r.status_code, len(r.text or "")))
        if reintentar and r.status_code in (403, 503):
            _log("  bloqueado (%s). Reintento con User-Agent de escritorio..." % r.status_code)
            r2 = _pedir(HEADERS_ESCRITORIO)
            _log("  -> HTTP %s (%s bytes)" % (r2.status_code, len(r2.text or "")))
            if r2.status_code == 200:
                return r2
            if IMPERSONAR:
                _log("  reintento con otra huella (chrome131)...")
                try:
                    r3 = _http.get(url, headers=HEADERS_ESCRITORIO,
                                   timeout=timeout, impersonate="chrome131")
                    _log("  -> HTTP %s (%s bytes)" % (r3.status_code, len(r3.text or "")))
                    if r3.status_code == 200:
                        return r3
                except Exception as e:
                    _log("  fallo el reintento: %s" % e)
        return r
    except requests.exceptions.SSLError as e:
        _log("GET %s -> ERROR SSL (antivirus/proxy interceptando?): %s" % (url, e))
        return None
    except requests.exceptions.ConnectionError as e:
        _log("GET %s -> SIN CONEXIÓN / DNS: %s" % (url, str(e)[:180]))
        return None
    except requests.exceptions.Timeout:
        _log("GET %s -> TIMEOUT (%ss)" % (url, timeout))
        return None
    except Exception as e:
        _log("GET %s -> %s: %s" % (url, type(e).__name__, str(e)[:180]))
        return None

# ---------------------------------------------------------------------------
# BÚSQUEDA
# ---------------------------------------------------------------------------
def _candidatos_directos(query):
    palabras = query.split()
    candidatos = []
    for i in range(len(palabras) - 1, 0, -1):
        artista = slugificar(" ".join(palabras[:i]))
        cancion = slugificar(" ".join(palabras[i:]))
        if artista and cancion:
            candidatos.append(f"{BASE}/{artista}/{cancion}/")
    return candidatos

def _es_pagina_de_cifra(resp):
    if resp is None or resp.status_code != 200:
        return False
    return ("<pre" in resp.text) or ("cifra_cnt" in resp.text)

def _desde_pagina_artista(query):
    palabras = query.split()
    objetivo = slugificar(" ".join(palabras[1:])) if len(palabras) > 1 else ""

    for i in range(len(palabras) - 1, 0, -1):
        artista = slugificar(" ".join(palabras[:i]))
        if not artista:
            continue
        resp = _get(f"{BASE}/{artista}/")
        if resp is None or resp.status_code != 200:
            continue

        slugs = set(re.findall(r"/" + re.escape(artista) + r"/([a-z0-9\-]+)/?[\"']",
                               resp.text))
        if not slugs:
            continue

        resto = slugificar(" ".join(palabras[i:]))
        if not resto:
            continue

        if resto in slugs:
            return f"{BASE}/{artista}/{resto}/"
        for s in slugs:
            if s.startswith(resto):
                return f"{BASE}/{artista}/{s}/"
        for s in slugs:
            if s in resto:
                return f"{BASE}/{artista}/{s}/"
        primera = resto.split('-')[0]
        if len(primera) >= 4:
            for s in slugs:
                if s.split('-')[0] == primera:
                    return f"{BASE}/{artista}/{s}/"
    return None

def buscar_url(query):
    query = (query or "").strip()
    if not query:
        return None

    if "cifraclub.com" in query:
        url = query if query.startswith("http") else "https://" + query
        url = url.replace("cifraclub.com/", "cifraclub.com.br/")
        if not url.endswith("/"):
            url += "/"
        return url if _es_pagina_de_cifra(_get(url)) else None

    for url in _candidatos_directos(query):
        if _es_pagina_de_cifra(_get(url)):
            return url

    url = _desde_pagina_artista(query)
    if url and _es_pagina_de_cifra(_get(url)):
        return url

    return None

# ---------------------------------------------------------------------------
# EXTRACCIÓN Y ANÁLISIS
# ---------------------------------------------------------------------------
def es_tablatura(linea):
    s = linea.strip()
    if not s:
        return False
    if any(s.startswith(p) for p in
           ('e|', 'b|', 'g|', 'd|', 'a|', 'E|', 'B|', 'G|', 'D|', 'A|',
            'e-', 'b-', 'g-', 'd-', 'a-', 'E-', 'B-', 'G-', 'D-', 'A-')):
        return True
    if '|' in s and s.count('-') >= 3:
        return True
    return False

def es_linea_de_acordes(linea):
    limpia = linea.strip()
    if not limpia or (limpia.startswith('[') and limpia.endswith(']')):
        return False
    palabras = limpia.split()
    if not palabras:
        return False
    coincidencias = sum(1 for p in palabras
                        if PATRON_ACORDE.match(p.strip('()[]{}|')))
    return (coincidencias / len(palabras)) >= 0.5

def extraer_acordes_unicos(cifra_texto):
    encontrados = []
    for linea in cifra_texto.split('\n'):
        if es_tablatura(linea) or not es_linea_de_acordes(linea):
            continue
        for palabra in linea.split():
            acorde = palabra.strip('[]{}|').strip()
            if PATRON_ACORDE.match(acorde) and acorde not in encontrados:
                encontrados.append(acorde)
    return encontrados

def _limpiar_nombre(texto):
    partes = [p.strip() for p in texto.split(' - ') if p.strip()]
    partes = [p for p in partes if 'cifra club' not in p.lower()]
    if len(partes) >= 2:
        return partes[0], partes[1]
    return (partes[0] if partes else ""), ""

def obtener_cifra(url):
    resp = _get(url)
    if resp is None or resp.status_code != 200:
        return {"ok": False, "error": "No se pudo conectar con Cifra Club.\n"
                                      "Revisá tu conexión a internet."}

    soup = BeautifulSoup(resp.text, "html.parser")

    cancion = artista = ""
    if soup.title:
        cancion, artista = _limpiar_nombre(soup.title.get_text().strip())

    partes = [p for p in url.split("/") if p and "cifraclub" not in p]
    if not cancion and len(partes) >= 2:
        artista = partes[-2].replace("-", " ").title()
        cancion = partes[-1].replace("-", " ").title()

    pre = soup.find("pre") or soup.find("div", class_="cifra_cnt")
    if pre is None:
        return {"ok": False, "error": "La página no tiene el formato esperado.\n"
                                      "Puede que Cifra Club haya cambiado el sitio."}

    texto = limpiar_texto(pre.get_text())

    lineas = [l for l in texto.split("\n") if not es_tablatura(l)]
    if not any(es_linea_de_acordes(l) for l in lineas):
        return {"ok": False, "error": "Esa página es solo la letra, no tiene acordes."}

    return {
        "ok": True,
        "error": None,
        "titulo": f"{artista} - {cancion}" if artista and cancion else cancion,
        "artista": artista,
        "cancion": cancion,
        "texto": texto,
        "acordes": extraer_acordes_unicos(texto),
        "url": url,
    }

# ---------------------------------------------------------------------------
# DIBUJO DE DIAGRAMAS
# ---------------------------------------------------------------------------
NOTAS = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
         'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10,
         'Bb': 10, 'B': 11}

CALIDADES = {
    '': 'maj', 'maj': 'maj', 'M': 'maj', '5': '5',
    'm': 'min', 'min': 'min', 'mim': 'min',
    '7': '7', '7M': 'maj7', 'maj7': 'maj7', 'M7': 'maj7', 'm7': 'm7',
    'min7': 'm7', '6': '6', 'm6': 'm6',
    'sus4': 'sus4', 'sus': 'sus4', 'sus2': 'sus2',
    'dim': 'dim', 'º': 'dim', '°': 'dim', 'dim7': 'dim7',
    'aug': 'aug', '+': 'aug', '5+': 'aug', 'aug5': 'aug',
    'add9': 'maj', '9': '7', 'm9': 'm7', '11': '7', '13': '7',
    'm7b5': 'm7', '7sus4': 'sus4', '4': 'sus4',
}

FORMA_E = {
    'maj':  [0, 2, 2, 1, 0, 0], 'min': [0, 2, 2, 0, 0, 0],
    '7':    [0, 2, 0, 1, 0, 0], 'm7':  [0, 2, 0, 0, 0, 0],
    'maj7': [0, 2, 1, 1, 0, 0], '6':   [0, 2, 1, 2, 0, 0],
    'm6':   [0, 2, 0, 0, 1, 0], 'sus4': [0, 2, 2, 2, 0, 0],
    'sus2': [0, 2, 4, 4, 0, 0], '5':   [0, 2, 2, -1, -1, -1],
    'dim':  [0, 1, 2, 0, 2, -1], 'dim7': [0, 1, 2, 0, 2, 0],
    'aug':  [0, 3, 2, 1, 1, 0],
}
FORMA_A = {
    'maj':  [-1, 0, 2, 2, 2, 0], 'min': [-1, 0, 2, 2, 1, 0],
    '7':    [-1, 0, 2, 0, 2, 0], 'm7':  [-1, 0, 2, 0, 1, 0],
    'maj7': [-1, 0, 2, 1, 2, 0], '6':   [-1, 0, 2, 2, 1, 2],
    'm6':   [-1, 0, 2, 2, 1, 2], 'sus4': [-1, 0, 2, 2, 3, 0],
    'sus2': [-1, 0, 2, 2, 0, 0], '5':   [-1, 0, 2, 2, -1, -1],
    'dim':  [-1, 0, 1, 2, 1, -1], 'dim7': [-1, 0, 1, 2, 1, 2],
    'aug':  [-1, 0, 3, 2, 2, 1],
}

def _partir_acorde(nombre):
    n = (nombre or '').strip()
    n = re.sub(r'\([^)]*\)', '', n)
    n = n.split('/')[0].strip()
    m = re.match(r'^([A-G][b#]?)(.*)$', n)
    if not m:
        return None, None
    return m.group(1), m.group(2).strip()

def voicing(nombre):
    if nombre in DIC_ACORDES:
        return DIC_ACORDES[nombre]

    raiz, sufijo = _partir_acorde(nombre)
    if raiz is None or raiz not in NOTAS:
        return None

    calidad = CALIDADES.get(sufijo)
    if calidad is None:
        for clave in sorted(CALIDADES, key=len, reverse=True):
            if clave and sufijo.startswith(clave):
                calidad = CALIDADES[clave]
                break
    if calidad is None:
        calidad = 'maj'

    semitonos = NOTAS[raiz]
    traste_e = (semitonos - NOTAS['E']) % 12
    traste_a = (semitonos - NOTAS['A']) % 12

    forma, traste = ((FORMA_E, traste_e) if traste_e <= 5
                     else (FORMA_A, traste_a))
    plantilla = forma.get(calidad, forma['maj'])

    posiciones = []
    for p in plantilla:
        if p <= 0:
            posiciones.append(p)
        else:
            posiciones.append(p + traste)
    return posiciones

def crear_diagrama_acorde(nombre):
    d = Drawing(58, 70)
    d.add(String(29, 58, nombre, fontName='Helvetica-Bold', fontSize=9,
                 textAnchor='middle', fillColor=colors.HexColor('#1A237E')))

    x_ini, y_ini = 10, 12
    w, h = 38, 40

    d.add(Rect(x_ini, y_ini, w, h, fillColor=colors.white,
               strokeColor=colors.HexColor('#333333'), strokeWidth=1))

    for i in range(1, 5):
        cx = x_ini + (w / 5) * i
        d.add(Line(cx, y_ini, cx, y_ini + h,
                   strokeColor=colors.HexColor('#BBBBBB'), strokeWidth=0.4))
    for j in range(1, 5):
        cy = y_ini + (h / 5) * j
        d.add(Line(x_ini, cy, x_ini + w, cy,
                   strokeColor=colors.HexColor('#CCCCCC'), strokeWidth=0.4))

    posiciones = voicing(nombre)
    if not posiciones:
        d.add(String(x_ini + w / 2, y_ini + h / 2 - 3, "?",
                     fontName='Helvetica-Bold', fontSize=16, textAnchor='middle',
                     fillColor=colors.HexColor('#999999')))
        return d

    base = 1
    reales = [p for p in posiciones if p > 0]
    if reales and min(reales) > 5:
        base = min(reales)
        posiciones = [p - (base - 1) if p > 0 else p for p in posiciones]

    if base > 1:
        d.add(String(x_ini - 2, y_ini + h - 6, f"{base}º", fontName='Helvetica-Bold',
                     fontSize=6, textAnchor='end',
                     fillColor=colors.HexColor('#555555')))

    for idx, traste in enumerate(posiciones):
        cx = x_ini + (w / 5) * idx
        if traste == 0:
            d.add(String(cx, y_ini + h + 2, "o", fontName='Helvetica-Bold',
                         fontSize=7, textAnchor='middle',
                         fillColor=colors.HexColor('#333333')))
        elif traste == -1:
            d.add(String(cx, y_ini + h + 2, "x", fontName='Helvetica-Bold',
                         fontSize=7, textAnchor='middle',
                         fillColor=colors.HexColor('#D32F2F')))
        elif 1 <= traste <= 5:
            cy = (y_ini + h) - (h / 10) - ((traste - 1) * (h / 5))
            d.add(Circle(cx, cy, 3.2, fillColor=colors.HexColor('#1A237E'),
                         strokeColor=None))
    return d

# ---------------------------------------------------------------------------
# GENERACIÓN DEL PDF (CON AUTO-AJUSTE Y COMPRESIÓN)
# ---------------------------------------------------------------------------
def compactar_linea_acordes(linea, max_len=32):
    """
    Si una línea de acordes supera max_len caracteres, reduce los espacios sobrantes
    entre acordes a 1 o 2 espacios para asegurar que quede en una única línea.
    """
    if len(linea) <= max_len:
        return linea
    
    parts = re.split(r'(\s+)', linea)
    new_parts = []
    for p in parts:
        if p.isspace():
            if len(p) > 2:
                new_parts.append("  ")
            else:
                new_parts.append(p)
        else:
            new_parts.append(p)
    return "".join(new_parts)

def crear_paragraph_ajustado(texto, es_acorde, col_width, base_size, base_leading, font_name, text_color):
    """
    Ajusta dinámicamente el tamaño de fuente si la línea supera el ancho de la columna.
    """
    texto_eval = re.sub(r'<[^>]+>', '', texto).replace('&nbsp;', ' ')
    dummy_canvas = canvas.Canvas(None)
    
    current_size = base_size
    current_leading = base_leading
    
    while current_size >= 7.5:
        width = dummy_canvas.stringWidth(texto_eval, font_name, current_size)
        if width <= col_width or current_size == 7.5:
            break
        current_size -= 0.5
        current_leading = current_size * 1.15

    style = ParagraphStyle(
        'AutoStyle',
        fontName=font_name,
        fontSize=current_size,
        leading=current_leading,
        textColor=text_color,
        spaceAfter=1
    )
    
    if es_acorde:
        return Paragraph(f"<b>{texto}</b>", style)
    else:
        return Paragraph(texto, style)

def generar_pdf(datos, ruta_destino, incluir_diagramas=True):
    # Márgenes reducidos a 7mm para aprovechar al máximo la hoja A4
    margin = 7 * mm
    doc = SimpleDocTemplate(
        ruta_destino, pagesize=A4,
        leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin,
        title=datos.get("titulo", "Cifra"),
    )

    page_width, page_height = A4
    printable_width = page_width - 2 * margin
    printable_height = page_height - 2 * margin

    header_height = 20 * mm
    body_height = printable_height - header_height
    col_width = (printable_width - 5 * mm) / 2

    frame_header = Frame(margin, margin + body_height, printable_width, header_height,
                         id='F_Header', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_col1 = Frame(margin, margin, col_width, body_height,
                       id='F_Col1', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_col2 = Frame(margin + col_width + 5 * mm, margin, col_width, body_height,
                       id='F_Col2', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    template = PageTemplate(id='TwoCol', frames=[frame_header, frame_col1, frame_col2])
    doc.addPageTemplates([template])

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'TituloBanda', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=14, leading=16, alignment=1, spaceAfter=2,
        textColor=colors.HexColor('#1A237E'))
    estilo_sub = ParagraphStyle(
        'SubTitulo', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=14, leading=16, alignment=1, spaceAfter=6,
        textColor=colors.HexColor('#333333'))
    estilo_seccion = ParagraphStyle(
        'Seccion', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=10, spaceBefore=6, spaceAfter=4,
        textColor=colors.HexColor('#1A237E'))

    story = []

    # Encabezado principal
    if datos.get("artista"):
        story.append(Paragraph(_html(datos["artista"].upper()), estilo_titulo))
        story.append(Paragraph(_html(datos["cancion"]), estilo_sub))
    else:
        story.append(Paragraph(_html(datos.get("titulo", "")), estilo_titulo))

    story.append(FrameBreak())

    # Procesamiento de líneas de letra y acordes
    lineas = [l for l in datos["texto"].split("\n") if not es_tablatura(l)]
    for idx, linea in enumerate(lineas):
        usar_12 = (idx % 2 == 0)
        base_size = 12.0 if usar_12 else 11.0
        base_leading = 13.5 if usar_12 else 12.5

        if es_linea_de_acordes(linea):
            linea_comp = compactar_linea_acordes(linea, max_len=32)
            linea_html = _html(linea_comp) or '&nbsp;'
            p = crear_paragraph_ajustado(
                linea_html, es_acorde=True, col_width=col_width,
                base_size=base_size, base_leading=base_leading,
                font_name='Courier-Bold', text_color=colors.HexColor('#0D1B6E')
            )
            story.append(p)
        else:
            linea_html = _html(linea) or '&nbsp;'
            p = crear_paragraph_ajustado(
                linea_html, es_acorde=False, col_width=col_width,
                base_size=base_size, base_leading=base_leading,
                font_name='Courier', text_color=colors.HexColor('#222222')
            )
            story.append(p)

    # Diagramas de acordes al final
    acordes = datos.get("acordes") or []
    if incluir_diagramas and acordes:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Acordes utilizados", estilo_seccion))

        filas, fila = [], []
        for idx, ac in enumerate(acordes):
            fila.append(crear_diagrama_acorde(ac))
            if len(fila) == 4 or idx == len(acordes) - 1:
                while len(fila) < 4:
                    fila.append("")
                filas.append(fila)
                fila = []

        tabla = Table(filas, hAlign='LEFT')
        tabla.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tabla)

    doc.build(story)
    return ruta_destino

def _html(texto):
    texto = (texto.replace('&', '&amp;')
                  .replace('<', '&lt;')
                  .replace('>', '&gt;'))
    return texto.replace(' ', '&nbsp;')

# ---------------------------------------------------------------------------
# FUNCIÓN MAESTRA
# ---------------------------------------------------------------------------
def procesar(consulta, incluir_diagramas=True, carpeta=None):
    consulta = (consulta or "").strip()
    if not consulta:
        return {"ok": False, "error": "Escribí el artista y el tema, o pegá un link."}

    del LOG[:]

    url = buscar_url(consulta)
    if not url:
        return {"ok": False, "error": _mensaje_fallo()}

    datos = obtener_cifra(url)
    if not datos["ok"]:
        return {"ok": False, "error": datos["error"]}

    carpeta = carpeta or carpeta_trabajo()
    base = slugificar(f"{datos['artista']} {datos['cancion']}") or "cifra"
    ruta = os.path.join(carpeta, f"{base}.pdf")

    contar = 1
    while os.path.exists(ruta):
        contar += 1
        ruta = os.path.join(carpeta, f"{base}-{contar}.pdf")

    try:
        generar_pdf(datos, ruta, incluir_diagramas)
    except Exception as e:
        return {"ok": False, "error": f"Error armando el PDF:\n{e}"}

    datos.update({"ok": True, "ruta": ruta, "error": None})
    return datos

def _mensaje_fallo():
    texto = "\n".join(LOG)
    if "SIN CONEXIÓN" in texto or "DNS" in texto:
        return ("No hay conexión con Cifra Club.\n"
                "Revisá internet, el firewall o el antivirus.\n\n"
                "Detalle:\n" + _ultima_linea_util())
    if "ERROR SSL" in texto:
        return ("Falla el certificado de seguridad.\n"
                "Casi siempre lo causa un antivirus o proxy que intercepta HTTPS.\n"
                "Probá desactivando el escaneo web del antivirus.\n\n"
                "Detalle:\n" + _ultima_linea_util())
    if "TIMEOUT" in texto:
        return ("Cifra Club no respondió a tiempo.\n"
                "Puede ser internet lenta o bloqueo del proveedor.\n\n"
                "Detalle:\n" + _ultima_linea_util())
    return ("No encontré esa canción.\nProbá \"Artista Tema\" separados por "
            "un espacio, o pegá el link de Cifra Club.\n\n"
            "Detalle:\n" + _ultima_linea_util())

def _ultima_linea_util():
    for linea in reversed(LOG):
        if "->" in linea:
            return linea[:300]
    return "(sin llamadas de red registradas)"

def diagnostico(consulta):
    del LOG[:]
    print("=" * 70)
    print("DIAGNOSTICO de:", consulta)
    print("=" * 70)

    import ssl
    print("Python     :", __import__("sys").version.split()[0])
    print("backend    :", BACKEND)
    print("version    :", VERSION_HTTP)
    try:
        import certifi
        print("certifi    :", certifi.where())
    except Exception:
        print("certifi    : NO INSTALADO")

    try:
        import socket
        ip = socket.gethostbyname("www.cifraclub.com.br")
        print("DNS        : www.cifraclub.com.br ->", ip)
    except Exception as e:
        print("DNS        : FALLA ->", e)

    print("-" * 70)
    url = buscar_url(consulta)
    for linea in LOG:
        print(" ", linea)
    print("-" * 70)

    if not url:
        print("RESULTADO  : no se obtuvo URL")
        print(_mensaje_fallo())
        return

    print("URL        :", url)
    datos = obtener_cifra(url)
    if datos["ok"]:
        print("TITULO     :", datos["titulo"])
        print("ACORDES    :", ", ".join(datos["acordes"]))
        print("RESULTADO  : OK")
    else:
        print("RESULTADO  : FALLO ->", datos["error"])

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if args and args[0] == "--diag":
        diagnostico(" ".join(args[1:]) or "coldplay sparks")
        raise SystemExit(0)

    q = " ".join(args) or "coldplay sparks"
    r = procesar(q)
    if r["ok"]:
        print("OK ->", r["ruta"])
        print("Acordes:", ", ".join(r["acordes"]))
    else:
        print("FALLO ->", r["error"])