## Despliegue detrás de Nginx

El formulario de ponentes permite subir hasta cinco imágenes. El límite de Flask
está fijado en 50 MB para el total de la solicitud, pero Nginx debe permitir al
menos ese tamaño; de lo contrario responde `413 Request Entity Too Large` antes
de que la solicitud llegue a Flask.

Dentro del bloque `server` del sitio, añade:

```nginx
client_max_body_size 50M;
```

Después valida y recarga Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

La directiva también puede ponerse dentro del `location` que proxifica a Flask,
si se quiere limitar solo esa ruta:

```nginx
location /admin/ponentes {
	client_max_body_size 50M;
	proxy_pass http://127.0.0.1:8000;
}
```

