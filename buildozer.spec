[app]

# ---------------------------------------------------------------- identidad --
title = Cifra a PDF

# El "nombre tecnico" de la app. Sin mayusculas ni espacios.
package.name = cifraapdf
package.domain = com.cifraapdf

# De donde salen los archivos
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json,txt

version = 7.0

# ------------------------------------------------------------------ python --
# OJO: si agregas una libreria al codigo, agregala tambien aca.
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna,beautifulsoup4,soupsieve,reportlab,pillow,android

# ---------------------------------------------------------------- pantalla ---
orientation = portrait
fullscreen = 0

# ------------------------------------------------------------------- iconos --
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png

# ------------------------------------------------------------------ android --
# INTERNET: para entrar a Cifra Club.
# WRITE/READ: para dejar el PDF en Descargas/CifraApp.
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API 29 a proposito: permite escribir en la carpeta publica Descargas
# sin las complicaciones de almacenamiento de Android 11+.
android.api = 29
android.minapi = 24
android.ndk = 25b

# arm64-v8a = telefonos modernos (la mayoria). Si tu telefono es viejo (32 bits)
# agrega ", armeabi-v7a" al final. Cada arquitectura duplica el tiempo de build.
android.archs = arm64-v8a

android.accept_sdk_license = True
android.allow_backup = True
android.wakelock = True

[buildozer]
log_level = 2
warn_on_root = 0
