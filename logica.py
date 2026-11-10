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

# ---------------------------------------------------------------------------
# GENERADOR DE PDF PROPIO  (sin dependencias: Python puro de punta a punta)
# ---------------------------------------------------------------------------
AZUL = (26, 35, 126)
TINTA_PDF = (34, 34, 34)
_MM = 72.0 / 25.4              # 1 mm en puntos
_A4_ANCHO, _A4_ALTO = 210.0, 297.0

_HELV_BOLD = {
    32: 0.278, 33: 0.333, 34: 0.474, 35: 0.556, 36: 0.556, 37: 0.889, 38: 0.722, 39: 0.238,
    40: 0.333, 41: 0.333, 42: 0.389, 43: 0.584, 44: 0.278, 45: 0.333, 46: 0.278, 47: 0.278,
    48: 0.556, 49: 0.556, 50: 0.556, 51: 0.556, 52: 0.556, 53: 0.556, 54: 0.556, 55: 0.556,
    56: 0.556, 57: 0.556, 58: 0.333, 59: 0.333, 60: 0.584, 61: 0.584, 62: 0.584, 63: 0.611,
    64: 0.975, 65: 0.722, 66: 0.722, 67: 0.722, 68: 0.722, 69: 0.667, 70: 0.611, 71: 0.778,
    72: 0.722, 73: 0.278, 74: 0.556, 75: 0.722, 76: 0.611, 77: 0.833, 78: 0.722, 79: 0.778,
    80: 0.667, 81: 0.778, 82: 0.722, 83: 0.667, 84: 0.611, 85: 0.722, 86: 0.667, 87: 0.944,
    88: 0.667, 89: 0.667, 90: 0.611, 91: 0.333, 92: 0.278, 93: 0.333, 94: 0.584, 95: 0.556,
    96: 0.333, 97: 0.556, 98: 0.611, 99: 0.556, 100: 0.611, 101: 0.556, 102: 0.333, 103: 0.611,
    104: 0.611, 105: 0.278, 106: 0.278, 107: 0.556, 108: 0.278, 109: 0.889, 110: 0.611, 111: 0.611,
    112: 0.611, 113: 0.611, 114: 0.389, 115: 0.556, 116: 0.333, 117: 0.611, 118: 0.556, 119: 0.778,
    120: 0.556, 121: 0.556, 122: 0.500, 123: 0.389, 124: 0.280, 125: 0.389, 126: 0.584,
}


def _ancho_helv_mm(texto, tam):
    total = 0.0
    for ch in texto:
        total += _HELV_BOLD.get(ord(ch), 556)
    return total / 1000.0 * tam / _MM


def _escape_pdf(texto):
    """Texto -> bytes escapados para un string PDF (gana acentos, pierde nada)."""
    b = (texto or "").encode("cp1252", "replace")
    salida = []
    for ch in b:
        if ch in (0x28, 0x29, 0x5C):
            salida.append("\\" + chr(ch))
        elif ch < 32 or ch > 126:
            salida.append("\\%03o" % ch)
        else:
            salida.append(chr(ch))
    return "".join(salida)


class _PDF(object):
    """Escritor de PDF minimo: A4, texto, lineas, rectangulos y circulos."""

    def __init__(self):
        self.paginas = []
        self.buf = None
        self.add_page()

    def add_page(self):
        self.buf = []
        self.paginas.append(self.buf)

    def _x(self, x_mm):
        return x_mm * _MM

    def _y(self, y_mm):
        return (_A4_ALTO - y_mm) * _MM

    def texto(self, x, y, txt, fuente="F1", tam=11.0, color=TINTA_PDF):
        if not txt:
            return
        self.buf.append(
            "BT /%s %.2f Tf %.3f %.3f %.3f rg 1 0 0 1 %.2f %.2f Tm (%s) Tj ET"
            % (fuente, tam, color[0] / 255.0, color[1] / 255.0,
               color[2] / 255.0, self._x(x), self._y(y), _escape_pdf(txt)))

    def linea(self, x1, y1, x2, y2, ancho=0.2, color=(51, 51, 51)):
        self.buf.append(
            "%.3f %.3f %.3f RG %.2f w %.2f %.2f m %.2f %.2f l S"
            % (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, ancho,
               self._x(x1), self._y(y1), self._x(x2), self._y(y2)))

    def rect(self, x, y, w, h, ancho=0.35, color=(51, 51, 51)):
        self.buf.append(
            "%.3f %.3f %.3f RG %.2f w %.2f %.2f %.2f %.2f re S"
            % (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, ancho,
               self._x(x), self._y(y + h), w * _MM, h * _MM))

    def circulo(self, cx, cy, r, color=AZUL):
        k = 0.5523 * r
        pt = lambda px, py: "%.2f %.2f" % (self._x(px), self._y(py))
        d = "%s m " % pt(cx, cy - r)
        d += "%s %s %s c " % (pt(cx + k, cy - r), pt(cx + r, cy - k), pt(cx + r, cy))
        d += "%s %s %s c " % (pt(cx + r, cy + k), pt(cx + k, cy + r), pt(cx, cy + r))
        d += "%s %s %s c " % (pt(cx - k, cy + r), pt(cx - r, cy + k), pt(cx - r, cy))
        d += "%s %s %s c f" % (pt(cx - r, cy - k), pt(cx - k, cy - r), pt(cx, cy - r))
        self.buf.append("%.3f %.3f %.3f rg %s"
                        % (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, d))

    def guardar(self, ruta):
        n = len(self.paginas)
        cont_ids, pag_ids = [], []
        siguiente = 6
        for _ in range(n):
            cont_ids.append(siguiente)
            siguiente += 1
            pag_ids.append(siguiente)
            siguiente += 1

        objs = [None] * siguiente
        objs[1] = "<< /Type /Catalog /Pages 2 0 R >>"
        objs[2] = ("<< /Type /Pages /Kids [%s] /Count %d >>"
                   % (" ".join("%d 0 R" % i for i in pag_ids), n))
        objs[3] = ("<< /Type /Font /Subtype /Type1 /BaseFont /Courier"
                   " /Encoding /WinAnsiEncoding >>")
        objs[4] = ("<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold"
                   " /Encoding /WinAnsiEncoding >>")
        objs[5] = ("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold"
                   " /Encoding /WinAnsiEncoding >>")

        fuentes = ("<< /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >>")
        for i, buf in enumerate(self.paginas):
            stream = "\n".join(buf)
            objs[cont_ids[i]] = ("<< /Length %d >>\nstream\n%s\nendstream"
                                 % (len(stream), stream))
            objs[pag_ids[i]] = (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f]"
                " /Resources %s /Contents %d 0 R >>"
                % (_A4_ANCHO * _MM, _A4_ALTO * _MM, fuentes, cont_ids[i]))

        cabecera = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        partes = [cabecera]
        pos = len(cabecera)
        offsets = [0] * siguiente
        for i in range(1, siguiente):
            cuerpo = ("%d 0 obj\n%s\nendobj\n" % (i, objs[i])).encode("latin-1")
            offsets[i] = pos
            partes.append(cuerpo)
            pos += len(cuerpo)

        xref = pos
        cola = ["xref\n0 %d\n" % siguiente, "0000000000 65535 f \n"]
        for i in range(1, siguiente):
            cola.append("%010d 00000 n \n" % offsets[i])
        cola.append("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                    % (siguiente, xref))
        partes.append("".join(cola).encode("latin-1"))

        with open(ruta, "wb") as f:
            f.write(b"".join(partes))


def compactar_linea_acordes(linea, max_len=32):
    """Si una linea de acordes es muy larga, reduce los espacios sobrantes."""
    if len(linea) <= max_len:
        return linea
    partes = re.split(r'(\s+)', linea)
    nuevo = []
    for p in partes:
        if p.isspace():
            nuevo.append("  " if len(p) > 2 else p)
        else:
            nuevo.append(p)
    return "".join(nuevo)


def _dibujar_diagrama(pdf, x, y, nombre, ancho):
    """Dibuja un diagrama de acorde. (x, y) = esquina superior izquierda."""
    alto = ancho * 1.12
    x0 = x + ancho * 0.15
    y0 = y + alto * 0.30
    w = ancho * 0.70
    h = alto * 0.55

    pdf.texto(x + (ancho - 0.6 * 9 * len(nombre) / _MM) / 2, y + alto * 0.11,
              nombre, fuente="F2", tam=9, color=AZUL)

    pdf.rect(x0, y0, w, h, ancho=0.35, color=(51, 51, 51))
    for i in range(1, 5):
        pdf.linea(x0 + w / 5 * i, y0, x0 + w / 5 * i, y0 + h,
                  ancho=0.15, color=(187, 187, 187))
    for j in range(1, 5):
        pdf.linea(x0, y0 + h / 5 * j, x0 + w, y0 + h / 5 * j,
                  ancho=0.15, color=(187, 187, 187))

    posiciones = voicing(nombre)
    if not posiciones:
        pdf.texto(x0 + w / 2 - 1.5, y0 + h / 2 + 1.5, "?",
                  fuente="F2", tam=14, color=(153, 153, 153))
        return

    base = 1
    reales = [p for p in posiciones if p > 0]
    if reales and min(reales) > 5:
        base = min(reales)
        posiciones = [p - (base - 1) if p > 0 else p for p in posiciones]

    if base > 1:
        etiqueta = "%do" % base
        pdf.texto(x0 - 0.8 - 0.6 * 6 * len(etiqueta) / _MM, y0 + 1.5,
                  etiqueta, fuente="F2", tam=6, color=(85, 85, 85))

    r = max(0.9, ancho * 0.045)
    for idx, traste in enumerate(posiciones):
        cx = x0 + (w / 5) * idx
        if traste == 0 or traste == -1:
            marca = "o" if traste == 0 else "x"
            color = (51, 51, 51) if traste == 0 else (211, 47, 47)
            pdf.texto(cx - 0.6 * 7 / _MM / 2, y0 - 0.8, marca,
                      fuente="F2", tam=7, color=color)
        elif 1 <= traste <= 5:
            cy = (y0 + h) - (h / 10) - ((traste - 1) * (h / 5))
            pdf.circulo(cx, cy, r, color=AZUL)


def generar_pdf(datos, ruta_destino, incluir_diagramas=True):
    pdf = _PDF()

    M = 7.0
    SEP = 5.0
    COL_W = (_A4_ANCHO - 2 * M - SEP) / 2.0
    COL_X = (M, M + COL_W + SEP)
    TOPE = _A4_ALTO - M
    TOP_CUERPO = M + 21.0
    PT = 1.0 / _MM              # punto -> mm

    # --- encabezado -------------------------------------------------------
    if datos.get("artista"):
        cabecera = [(datos["artista"].upper(), AZUL),
                    (datos["cancion"], (51, 51, 51))]
    else:
        cabecera = [(datos.get("titulo", ""), AZUL)]

    y_cab = M + 1
    for texto, color in cabecera:
        ancho = _ancho_helv_mm(texto, 14)
        pdf.texto((_A4_ANCHO - ancho) / 2, y_cab + 5, texto,
                  fuente="F3", tam=14, color=color)
        y_cab += 7.5

    pdf.linea(M, y_cab + 2.5, _A4_ANCHO - M, y_cab + 2.5,
              ancho=0.2, color=(200, 205, 215))

    # --- letra y acordes en dos columnas ----------------------------------
    lineas = [l for l in datos["texto"].split("\n") if not es_tablatura(l)]

    col = 0
    y = TOP_CUERPO
    top = TOP_CUERPO

    for linea in lineas:
        es_acorde = es_linea_de_acordes(linea)
        texto = compactar_linea_acordes(linea, 44) if es_acorde else linea
        if not texto:
            texto = " "

        tam = 11.5
        ancho = 0.6 * tam * len(texto) / _MM          # Courier: ancho fijo
        while tam > 7.0 and ancho > COL_W - 1.5:
            tam -= 0.5
            ancho = 0.6 * tam * len(texto) / _MM
        salto = tam * 1.20 * PT

        if y + salto > TOPE:
            if col == 0:
                col = 1
                y = top
            else:
                pdf.add_page()
                col = 0
                top = M
                y = top

        pdf.texto(COL_X[col], y + tam * 0.82 * PT, texto,
                  fuente="F2" if es_acorde else "F1", tam=tam,
                  color=AZUL if es_acorde else TINTA_PDF)
        y += salto

    # --- diagramas de acordes al final ------------------------------------
    acordes = datos.get("acordes") or []
    if incluir_diagramas and acordes:
        ancho_celda = (_A4_ANCHO - 2 * M) / 4.0
        d_ancho = ancho_celda * 0.78
        alto_fila = d_ancho * 1.12 + 2.5
        filas = (len(acordes) + 3) // 4
        necesario = 10 + filas * alto_fila

        if col != 0 or y + necesario > TOPE:
            pdf.add_page()
            col = 0
            y = M

        y += 4
        pdf.texto(M, y + 3, "Acordes utilizados", fuente="F3", tam=10, color=AZUL)
        y += 7

        for i, ac in enumerate(acordes):
            fi, ci = divmod(i, 4)
            _dibujar_diagrama(pdf, M + ci * ancho_celda, y + fi * alto_fila,
                              ac, d_ancho)

    pdf.guardar(ruta_destino)
    return ruta_destino


# ---------------------------------------------------------------------------
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
