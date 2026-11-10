# Cifra a PDF — versión Android

Guía pensada para que **no tengas que instalar nada en tu PC**. La APK se
compila gratis en GitHub, en la nube, con los archivos de esta carpeta.

---

## Qué cambió respecto a la versión Windows

| Antes (Windows) | Ahora (Android) | Por qué |
|---|---|---|
| `cifra_app.py` con **customtkinter** | **`main.py`** con Kivy | tkinter no existe en Android. La ventana es la misma: misma paleta, misma tarjeta, mismo botón verde. |
| `logica.py` | **`logica.py` — sin tocar** | Ya era código portable. Detecta Android solo y guarda en su carpeta privada. |
| `curl_cffi` (imitar Chrome) | se cae solo a `requests` | Probado: Cifra Club responde **HTTP 200** con `requests` y el User-Agent móvil. No hacía falta. |
| `filedialog` para elegir dónde guardar | guarda en **Descargas/CifraApp** | En Android no hay diálogo de "guardar como". |
| `os.startfile` para abrir el PDF | intent de Android | Abre tu lector de PDF. |
| `messagebox` | etiqueta de estado + registro | En Android no hay cuadros de mensaje. |

Lo que **no** cambió: la búsqueda, el parseo, los acordes y el PDF.
El PDF que genera esta versión es idéntico al de Windows.

---

## Paso 1 — Crear el repositorio en GitHub

1. Entrá a <https://github.com> e iniciá sesión (si no tenés cuenta, creá una).
2. Arriba a la derecha: **+** → **New repository**.
3. Nombre: `cifra-a-pdf`.
4. Marcá **Public** (importante: en repos públicos los minutos de compilación son **ilimitados y gratis**).
5. **No** marques "Add a README".
6. **Create repository**.

---

## Paso 2 — Subir esta carpeta

### Opción A (la más rápida)

1. Descomprimí el ZIP en una carpeta.
2. Abrí la carpeta.
3. En Windows: pestaña **Vista** → tildá **Elementos ocultos**. Hace falta ver `.github`.
4. **Ctrl + A** para seleccionar todo (incluida la carpeta `.github`).
5. En la página del repo en GitHub: **Add file** → **Upload files**.
6. **Arrastrá** lo seleccionado a la ventana del navegador. Arrastrá el
   *contenido*, no la carpeta de arriba: los archivos tienen que quedar en la
   raíz del repositorio, con `.github` en la raíz.
7. Abajo: **Commit changes**.

### Opción B (si la A no te sale)

Subí el contenido de a uno y creá el workflow a mano:

1. **Add file** → **Upload files** → arrastrá `main.py`, `logica.py`,
   `buildozer.spec`, `icon.png`, `.gitignore`, `requirements-desktop.txt`.
2. **Add file** → **Create new file**.
3. En el nombre escribí exactamente:

       .github/workflows/build-apk.yml

   GitHub crea las carpetas solo al escribir las barras.
4. Pegá el contenido de `.github/workflows/build-apk.yml` y confirmá.

### Verificación obligatoria antes de seguir

En la lista de archivos del repositorio tiene que aparecer la carpeta
**`.github`**. Si no está, GitHub nunca va a compilar nada y la pestaña Actions
va a quedar vacía: significa que el arrastre se salteó la carpeta oculta.
En ese caso usá la Opción B para crearla a mano.

Tiene que quedar así, en la raíz:

    .github/workflows/build-apk.yml

---

## Paso 3 — Esperar la compilación

1. Andá a la pestaña **Actions** del repositorio.
2. Vas a ver corriendo **Compilar APK** (punto amarillo).
3. **La primera vez tarda entre 40 y 70 minutos.** Es normal: descarga y compila
   Python para Android. No cierres nada, podés irte.
4. Las siguientes veces, gracias al caché, tarda bastante menos (~10-20 min).

---

## Paso 4 — Descargar e instalar la APK

1. Cuando el punto esté **verde** ✅, entrá a esa ejecución.
2. Abajo, en **Artifacts**, descargá **Cifra-a-PDF-APK**.
3. Se baja un `.zip`. Adentro está `cifraapdf-7.0-arm64-v8a-debug.apk`.
4. Pasá la APK al teléfono (WhatsApp a tu propio chat, cable USB, Drive…).
5. En el teléfono, tocá la APK. Android va a pedirte permitir
   **"Instalar apps desconocidas"** para esa aplicación: aceptá.
6. Listo. El icono aparece en el cajón de apps.

Los PDFs quedan en **Descargas/CifraApp**, visibles desde cualquier gestor de
archivos o lector de PDF.

---

## Cómo actualizar la app más adelante

1. En GitHub, abrí el archivo que querés cambiar (`main.py` o `logica.py`).
2. Icono del lápiz (**Edit**).
3. Cambiás y apretás **Commit changes**.
4. GitHub recompila solo. En ~20 min tenés APK nueva en Actions.
5. **Subí el número** `version = 7.0` en `buildozer.spec` (ej: `7.1`) cada vez,
   si no Android puede negarse a actualizar encima de la anterior.

---

## Probar en la PC antes de compilar

Sirve para ver la interfaz sin esperar 1 hora:

    pip install -r requirements-desktop.txt
    python main.py

Aviso: en Windows `kivy` necesita además `pip install kivy[base]`, y la parte de
"Descargas" y "permisos" solo funciona en Android (en PC se ignora sin romper).

---

## Si el build falla (punto rojo ❌)

1. Entrá a la ejecución roja.
2. Desplegá el paso **3. Compilar el APK**.
3. Buscá la línea que empieza con `[ERROR]` o `Command failed`.
4. Los dos fallos más probables y su solución:

| Error en el log | Qué hacer |
|---|---|
| `reportlab` / `_rl_accel` | Reemplazar `reportlab` por `reportlab==3.6.13` en `requirements` de `buildozer.spec`. |
| `No module named ...` | Falta la librería en `requirements` de `buildozer.spec`. |

Si no lo entendés, copiame las últimas 30 líneas del log y lo arreglo.

---

## Archivos de esta carpeta

    main.py                     interfaz Android (reemplaza cifra_app.py)
    logica.py                   tu lógica, sin cambios
    buildozer.spec              configuración de la APK
    icon.png                    icono 512x512
    requirements-desktop.txt    para probar en la PC
    .github/workflows/          la receta de compilación en la nube
    .gitignore                  archivos que no se suben

Los viejos `.spec` de PyInstaller, los `.bat` y la carpeta `dist/` **no van**:
eran solo para Windows.
