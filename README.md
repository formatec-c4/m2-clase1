# Clínica Veterinaria Firulais — Práctica Replatform

Este repositorio corresponde al Módulo 2, Clase 1 del curso de Cloud Computing de FormaTEC / IPAP.

La práctica usa el caso de la Clínica Veterinaria Firulais para explicar una migración tipo **Replatform**: mejorar la plataforma de ejecución sin rediseñar completamente la lógica de negocio.

La frase guía de la clase:

```text
Migrar no es copiar servidores.
Migrar es decidir qué hacer con cada sistema según valor, riesgo, costo, esfuerzo y beneficio esperado.
```

## 1. Qué problema estamos simulando

Firulais tiene un sistema simple de turnos online. La aplicación funciona, pero queremos mejorar cómo se ejecuta.

Vamos a comparar dos versiones:

```text
Versión old
└── un contenedor con Flask + MySQL juntos

Versión replatform
├── un contenedor para Flask
└── un contenedor para MySQL
```

La lógica de negocio se mantiene:

- ver turnos;
- crear turnos;
- guardar turnos en MySQL.

Lo que cambia es la plataforma:

- antes todo está junto;
- después separamos aplicación y base de datos;
- movemos los datos con backup y restore;
- validamos que los datos se vean desde el front.

## 2. Conceptos mínimos antes de ejecutar

### Qué es Docker

Docker permite ejecutar una aplicación dentro de un **contenedor**.

Un contenedor incluye lo necesario para correr un proceso: sistema base, dependencias, archivos de la app y comando de inicio.

En esta práctica usamos contenedores para no depender de que cada alumno tenga instalado Python, Flask o MySQL en su máquina.

### Qué es una imagen

Una imagen es una plantilla para crear contenedores.

Ejemplo:

```text
Dockerfile
└── define cómo construir la imagen de la aplicación
```

Cuando ejecutamos:

```bash
docker compose up --build
```

Docker construye la imagen y después crea contenedores a partir de esa imagen.

### Qué es Docker Compose

Docker Compose permite definir varios servicios en un archivo YAML.

En lugar de ejecutar muchos comandos manuales, declaramos:

- qué contenedores existen;
- qué imagen usan;
- qué variables de entorno reciben;
- qué puertos exponen;
- qué volúmenes usan;
- qué servicio depende de cuál.

En este repositorio hay dos Compose:

```text
docker-compose.old.yml  -> versión old, todo junto
docker-compose.yml      -> versión replatform, app y db separadas
```

### Qué es un volumen

Un contenedor puede borrarse y volver a crearse. Si los datos importantes viven solo dentro del contenedor, se pierden.

Un volumen permite persistir datos fuera del ciclo de vida del contenedor.

En esta práctica:

```text
mysql_old_data -> datos MySQL de la versión old
mysql_data     -> datos MySQL de la versión replatform
```

### Qué es MySQL

MySQL es una base de datos relacional. Guarda información en tablas.

En esta práctica usamos una tabla llamada `turnos`.

Una fila representa un turno:

```text
id | mascota | duenio | fecha | hora | motivo | created_at
```

### Qué es Flask

Flask es un framework liviano de Python para crear aplicaciones web.

En esta práctica Flask expone:

```text
GET  /            -> página HTML para listar, crear, editar y borrar turnos
GET  /health      -> healthcheck de app + base de datos
GET  /api/turnos  -> lista turnos en JSON
POST /api/turnos  -> crea un turno
PUT  /api/turnos/:id -> actualiza un turno
DELETE /api/turnos/:id -> borra un turno
```

El servidor Python escucha en:

```text
0.0.0.0:8000
```

`0.0.0.0` significa que Flask acepta conexiones desde fuera del contenedor. Por eso podemos abrir la app desde el navegador en:

```text
http://localhost:8000
```

## 3. Estructura del proyecto

```text
m2-clase1/
├── app/
│   ├── app.py
│   └── templates/
│       └── index.html
├── db/
│   └── init.sql
├── dumps/
│   └── .gitkeep
├── scripts/
│   ├── backup_mysql.sh
│   ├── restore_mysql.sh
│   └── start-old.sh
├── Dockerfile
├── Dockerfile.old
├── docker-compose.yml
├── docker-compose.old.yml
└── requirements.txt
```

## 4. Cómo funciona la aplicación Python

El archivo principal es:

```text
app/app.py
```

La app lee la configuración de MySQL desde variables de entorno:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

Esto es importante porque el mismo código puede conectarse a:

```text
old:        MySQL en 127.0.0.1 dentro del mismo contenedor
replatform: MySQL en el servicio db de Docker Compose
```

La app no necesita cambiar. Cambia la configuración.

## 5. Cómo funciona la tabla de turnos

La tabla se crea desde:

```text
db/init.sql
```

El SQL principal es:

```sql
CREATE TABLE IF NOT EXISTS turnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mascota VARCHAR(100) NOT NULL,
    duenio VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    motivo TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

También se insertan dos turnos de ejemplo:

```sql
INSERT INTO turnos (mascota, duenio, fecha, hora, motivo)
VALUES
    ('Luna', 'Mariana', '2026-05-20', '09:30:00', 'Vacunacion anual'),
    ('Toby', 'Carlos', '2026-05-20', '11:00:00', 'Control general');
```

## 6. Versión old: todo junto

La versión old se ejecuta con:

```text
docker-compose.old.yml
```

Arquitectura:

```text
Contenedor firulais-legacy-app
├── Flask
└── MySQL
```

Levantar:

```bash
docker compose -f docker-compose.old.yml up --build
```

Abrir:

```text
http://localhost:8000
```

Abrir phpMyAdmin:

```text
http://localhost:8081
```

Credenciales:

```text
usuario: firulais
password: firulais
base: firulais
```

Qué observar:

- la página carga desde Flask;
- los turnos se leen desde MySQL;
- desde la página se puede crear, editar y borrar turnos;
- phpMyAdmin permite ver la base `firulais` y la tabla `turnos`;
- todo corre dentro de un mismo contenedor;
- los datos persisten en el volumen `mysql_old_data`.

### Operar turnos desde la app

Desde el navegador:

```text
http://localhost:8000
```

Usar el formulario para crear un turno.

Para editar, presionar `Editar` en una fila, cambiar los datos y guardar.

Para borrar, presionar `Borrar` en una fila y confirmar.

Cada acción usa la API Flask por debajo y guarda los cambios en MySQL.

### Validar por API

Healthcheck:

```bash
curl http://localhost:8000/health
```

Listar turnos:

```bash
curl http://localhost:8000/api/turnos
```

Crear turno por API:

```bash
curl -X POST http://localhost:8000/api/turnos \
  -H "Content-Type: application/json" \
  -d '{"mascota":"Nina","duenio":"Laura","fecha":"2026-05-22","hora":"15:00","motivo":"Chequeo previo a viaje"}'
```

Actualizar turno por API:

```bash
curl -X PUT http://localhost:8000/api/turnos/1 \
  -H "Content-Type: application/json" \
  -d '{"mascota":"Luna","duenio":"Mariana","fecha":"2026-05-21","hora":"09:45","motivo":"Control actualizado"}'
```

Borrar turno por API:

```bash
curl -X DELETE http://localhost:8000/api/turnos/2
```

Después refrescar el front:

```text
http://localhost:8000
```

Los cambios deberían verse en la tabla.

## 7. Mirar MySQL por dentro

La forma visual es abrir phpMyAdmin:

```text
http://localhost:8081
```

Desde ahí:

1. Entrar a la base `firulais`.
2. Abrir la tabla `turnos`.
3. Revisar columnas, filas e inserts.
4. Crear o editar un registro y luego refrescar `http://localhost:8000`.

También se puede entrar por terminal.

Entrar al contenedor old:

```bash
docker compose -f docker-compose.old.yml exec app mysql -u firulais -pfirulais firulais
```

Ver las tablas:

```sql
SHOW TABLES;
```

Ver la estructura de `turnos`:

```sql
DESCRIBE turnos;
```

Consultar datos:

```sql
SELECT id, mascota, duenio, fecha, hora, motivo FROM turnos;
```

Insertar un turno manualmente desde MySQL:

```sql
INSERT INTO turnos (mascota, duenio, fecha, hora, motivo)
VALUES ('Mora', 'Luis', '2026-05-23', '12:30:00', 'Consulta dermatologica');
```

Volver a consultar:

```sql
SELECT id, mascota, duenio, fecha, hora, motivo FROM turnos;
```

Salir:

```sql
exit
```

Refrescar `http://localhost:8000` y verificar que el turno agregado desde MySQL aparece en el front.

## 8. Persistencia en la versión old

Bajar los contenedores sin borrar volúmenes:

```bash
docker compose -f docker-compose.old.yml down
```

Volver a levantar:

```bash
docker compose -f docker-compose.old.yml up
```

Consultar:

```bash
curl http://localhost:8000/api/turnos
```

Los datos siguen porque el volumen `mysql_old_data` conserva la base.

Borrar contenedor y volumen:

```bash
docker compose -f docker-compose.old.yml down -v
```

Al levantar otra vez, MySQL se inicializa de nuevo con `db/init.sql`.

## 9. Backup de datos desde old

En una migración real no alcanza con levantar una plataforma nueva. Hay que mover los datos.

Crear backup:

```bash
docker compose -f docker-compose.old.yml exec app scripts/backup_mysql.sh
```

Esto crea:

```text
dumps/firulais-mysql-dump.sql
```

El script usa `mysqldump`, que genera un archivo SQL con la estructura y los datos.

Podés mirar el archivo:

```bash
sed -n '1,80p' dumps/firulais-mysql-dump.sql
```

Bajar la versión old:

```bash
docker compose -f docker-compose.old.yml down
```

## 10. Versión replatform: app y base separadas

La versión replatform se ejecuta con:

```text
docker-compose.yml
```

Arquitectura:

```text
Docker Compose
├── app: Flask
└── db: MySQL
```

Levantar:

```bash
docker compose up --build
```

Abrir:

```text
http://localhost:8000
```

Abrir phpMyAdmin:

```text
http://localhost:8081
```

Credenciales:

```text
usuario: firulais
password: firulais
base: firulais
```

Qué observar:

- Flask corre en el contenedor `firulais-new-app`;
- MySQL corre en el contenedor `firulais-new-db`;
- phpMyAdmin corre en el contenedor `firulais-new-phpmyadmin`;
- la app se conecta a MySQL usando `DB_HOST=db`;
- el CRUD sigue operando desde la misma pantalla web;
- los datos persisten en el volumen `mysql_data`.

## 11. Restaurar datos en replatform

Restaurar el backup:

```bash
docker compose exec app scripts/restore_mysql.sh
```

Validar por API:

```bash
curl http://localhost:8000/api/turnos
```

Validar visualmente:

```text
http://localhost:8000
```

Los turnos creados en la versión old deberían aparecer en la versión replatform.

## 12. Mirar MySQL separado

La forma visual es usar phpMyAdmin:

```text
http://localhost:8081
```

Ahí se puede inspeccionar la base `firulais`, abrir `turnos`, ver los datos restaurados y comprobar que los cambios hechos desde la app aparecen en la tabla.

Entrar al contenedor de base de datos:

```bash
docker compose exec db mysql -u firulais -pfirulais firulais
```

Consultar:

```sql
SHOW TABLES;
DESCRIBE turnos;
SELECT id, mascota, duenio, fecha, hora, motivo FROM turnos;
```

Salir:

```sql
exit
```

## 13. Persistencia en replatform

Bajar sin borrar volúmenes:

```bash
docker compose down
```

Volver a levantar:

```bash
docker compose up
```

Consultar:

```bash
curl http://localhost:8000/api/turnos
```

Los datos siguen porque MySQL usa el volumen `mysql_data`.

Borrar datos:

```bash
docker compose down -v
```

Al levantar nuevamente, MySQL vuelve a inicializarse desde `db/init.sql`.

## 14. Comparación old vs replatform

| Tema | Old | Replatform |
| --- | --- | --- |
| App | Flask dentro del mismo contenedor que MySQL | Flask en su propio contenedor |
| Base de datos | MySQL dentro del contenedor old | MySQL en contenedor separado |
| Configuración | `DB_HOST=127.0.0.1` | `DB_HOST=db` |
| Persistencia | volumen `mysql_old_data` | volumen `mysql_data` |
| Operación | app y base acopladas | app y base separadas |
| Migración de datos | origen del backup | destino del restore |

Esto es Replatform porque:

- no cambiamos la lógica de turnos;
- no cambiamos completamente la arquitectura de negocio;
- mejoramos la plataforma de ejecución;
- separamos responsabilidades;
- mantenemos MySQL para reducir riesgo;
- hacemos backup y restore para mover datos.

## 15. Preguntas de reflexión

1. ¿Qué cambió entre old y replatform?
2. ¿Qué se mantuvo igual desde el punto de vista del negocio?
3. ¿Por qué separar app y base de datos mejora la operación?
4. ¿Por qué las variables de entorno ayudan en una migración?
5. ¿Qué pasaría si borramos un contenedor pero no el volumen?
6. ¿Qué pasaría si borramos el volumen?
7. ¿Por qué migrar datos es tan importante como migrar la aplicación?
8. ¿Qué habría que validar después del restore?
9. ¿Por qué esto no es Rehost puro?
10. ¿Por qué esto no llega a ser Refactor?
11. ¿Qué faltaría para producción real?

## 16. Limpieza

Bajar old:

```bash
docker compose -f docker-compose.old.yml down -v
```

Bajar replatform:

```bash
docker compose down -v
```

Borrar dump generado:

```bash
rm -f dumps/firulais-mysql-dump.sql
```
