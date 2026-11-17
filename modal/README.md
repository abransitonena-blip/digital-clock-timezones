# AP Model 3D Foto en Modal

La misma página del notebook, pero en Modal: **GPU A100 de 80 GB, URL fija** y los modelos guardados en un volumen. No hay que ejecutar celdas cada vez.

## Pasos (una sola vez)

Puedes hacerlo desde tu computadora o desde una celda de Colab (agrega `!` delante de cada comando).

1. Instalar y entrar a tu cuenta de Modal (abre el navegador para aprobar):
   ```
   pip install modal
   python3 -m modal setup
   ```
2. Bajar el proyecto:
   ```
   git clone -b claude/practical-gates-go63pg https://github.com/abransitonena-blip/digital-clock-timezones
   cd digital-clock-timezones
   ```
3. Crear el secreto con la contraseña de la página (y, si quieres FLUX, tu token de Hugging Face):
   ```
   modal secret create ap3d PASSWORD=tu_contraseña
   # o con FLUX:  modal secret create ap3d PASSWORD=tu_contraseña HF_TOKEN=hf_xxx
   ```
4. Descargar los modelos al volumen (~80 GB, 10-20 min, solo la primera vez):
   ```
   modal run modal/modal_app.py::descargar_modelos
   ```
5. Publicar la página:
   ```
   modal deploy modal/modal_app.py
   ```
   Al terminar muestra la URL (`https://ap9871888--ap3d-web.modal.run` o parecida). Usuario **ap** y tu contraseña.

## Cómo funciona
- La primera vez que abres la URL, Modal enciende la A100 y carga los modelos (2-4 min). Después responde al momento.
- Si nadie la usa durante 15 min, se apaga sola y **deja de cobrar**. La siguiente visita la vuelve a encender.
- Los modelos generados y lo que el programa aprende se guardan en el volumen `ap3d-salidas`. No se pierden al apagarse.
- Para ver registros y uso: https://modal.com/apps

## Costo
Modal cobra la GPU por segundo solo mientras está encendida. La A100-80GB cuesta del orden de 2-3 USD por hora; revisa el precio actual en https://modal.com/pricing. Con el apagado automático pagas solo el tiempo que la usas, más 15 min.

## Actualizar
Cuando haya cambios en el proyecto: `git pull` y otra vez `modal deploy modal/modal_app.py`.
