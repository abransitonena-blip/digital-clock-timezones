# Herramientas

## mantener_activo_mac.command
Mantiene activa la página (Colab o Kaggle) desde tu Mac y la apagas cuando quieras.

1. Descarga el archivo (en GitHub: *Raw* → guardar) y dale permiso una vez:
   `chmod +x mantener_activo_mac.command`
2. Doble clic (la primera vez: clic derecho → Abrir) y pega la dirección de tu página.
3. **Apagar:** cierra la ventana de Terminal o pulsa `Ctrl+C`.

Mientras está abierta: la Mac no se duerme (la pestaña de Colab/Kaggle sigue
conectada), visita la página cada minuto y te avisa con una notificación si deja
de responder. Deja abierta la pestaña del notebook. Colab corta una sesión a las
24 h como máximo; para una página siempre encendida sin tu Mac, usa Modal (`modal/`).
