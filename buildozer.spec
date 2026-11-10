[app]

# ---------------------------------------------------------------- identidad --
title = Cifra a PDF
package.name = cifraapdf
package.domain = com.cifraapdf

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,txt

version = 7.0

# ------------------------------------------------------------------ python --
# p4a fijado a proposito: esa version usa Python 3.11.5, que es la que
# corresponde a Kivy 2.3.0. La master actual usa Python 3.14 y Kivy no compila.
p4a.branch = v2024.01.21

# Sin reportlab ni pillow: el PDF se genera con Python puro (logica.py).
# Cuantas menos cosas compilar, menos puede fallar.
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna,beautifulsoup4,soupsieve,android

# ---------------------------------------------------------------- pantalla ---
orientation = portrait
fullscreen = 0

# ------------------------------------------------------------------- iconos --
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png

# ------------------------------------------------------------------ android --
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API 29 permite escribir en la carpeta publica Descargas sin complicaciones.
android.api = 29
android.minapi = 24
android.ndk = 25b

# arm64-v8a = telefonos modernos. Si el tuyo es viejo (32 bits) agrega
# ", armeabi-v7a" (cada arquitectura duplica el tiempo de compilacion).
android.archs = arm64-v8a

android.accept_sdk_license = True
android.allow_backup = True
android.wakelock = True

[buildozer]
log_level = 2
warn_on_root = 0
