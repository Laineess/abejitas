# 🐝 AWS Students Builder — Pantalla interactiva

App para exposición: la instancia muestra en pantalla completa la leyenda
**AWS Students Builder** con los logos de AWS y la UAEMex, abejas volando y un
QR en la esquina inferior izquierda ("déjanos un mensaje"). El QR lleva a una
página donde el alumno escribe un mensaje (máx. 100 caracteres); si pasa el
filtro de groserías/discurso de odio, una abejita se detiene en la pantalla y
lo muestra en una burbuja.

## Estructura

```
aws-students-builder/
├── app.py              # servidor Flask (API + páginas)
├── moderacion.py       # filtro de groserías y discurso de odio
├── requirements.txt
├── templates/
│   ├── display.html    # pantalla principal (la instancia)
│   ├── mensaje.html    # página del QR (formulario del alumno)
│   └── admin.html      # panel del administrador
└── static/             # coloca aquí aws.png y uaemex.png (opcional)
```

## Correr localmente (prueba)

```bash
cd aws-students-builder
pip install -r requirements.txt
python app.py
```

- Pantalla principal: http://localhost:8080/
- Página del mensaje (a donde apunta el QR): http://localhost:8080/mensaje
- Panel admin: http://localhost:8080/admin — contraseña por defecto: `abejas2026`

## Configuración (variables de entorno)

| Variable         | Default        | Uso                                  |
|------------------|----------------|--------------------------------------|
| `PORT`           | `8080`         | Puerto del servidor                  |
| `ADMIN_PASSWORD` | `abejas2026`   | Contraseña del panel `/admin`        |
| `SECRET_KEY`     | (insegura)     | Clave de sesión Flask — cámbiala     |

## Reglas del sistema

- Mensajes de máximo **100 caracteres**.
- **Cooldown de 10 segundos** por visitante (por IP); los intentos con
  groserías también consumen el cooldown.
- Mensajes con groserías o discurso de odio se **rechazan** con una
  advertencia al alumno y quedan registrados en el log del servidor.
- El admin puede **activar/desactivar** la aparición de mensajes en la
  pantalla desde `/admin` (los mensajes se siguen guardando, solo se pausa
  su exhibición).
- El QR se genera solo (`/qr.png`) con la URL pública del servidor: al
  desplegar en EC2 apuntará automáticamente a la IP/dominio correcto.

## Notas para el despliegue en EC2 (resumen)

1. Instancia con Ubuntu, Security Group con puerto 80 (o el que uses) abierto.
2. `sudo apt update && sudo apt install -y python3-pip`
3. Copiar esta carpeta, `pip3 install -r requirements.txt`.
4. Producción: `pip3 install gunicorn` y
   `gunicorn -w 2 -b 0.0.0.0:80 app:app` (con `sudo` o vía systemd).
5. Abrir `http://IP-PUBLICA/` en la pantalla de la expo; el QR ya apunta a
   `http://IP-PUBLICA/mensaje`.

(Instrucciones detalladas de despliegue: pendientes, se darán con los datos
de la instancia.)
# abejitas
