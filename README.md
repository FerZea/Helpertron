# FinanceBot (Telegram + Google Sheets)

Bot personal de finanzas en Python para registrar gastos desde Telegram y guardarlos en Google Sheets.

Cuando envias un mensaje como `Uber 200`, el bot:
- interpreta descripcion y monto,
- asigna categoria automaticamente por reglas configurables,
- guarda una fila en Google Sheets con fecha/hora del mensaje.

## Que guarda en la hoja

Columnas generadas automaticamente:
- `timestamp_utc`
- `timestamp_local`
- `descripcion`
- `monto`
- `categoria`
- `moneda`
- `telegram_message_id`

`timestamp_utc` y `timestamp_local` salen del timestamp real del mensaje de Telegram (`message.date`).

## Requisitos

- Docker + Docker Compose (recomendado)
- Bot de Telegram creado en BotFather
- Proyecto en Google Cloud con `Google Sheets API` habilitada
- Cuenta de servicio (service account) con clave JSON
- Hoja de Google Sheets compartida con el correo de la cuenta de servicio

## Configuracion paso a paso

### 1) Crear/obtener token del bot

1. Abre BotFather en Telegram.
2. Crea bot con `/newbot` o rota token con `/token`.
3. Guarda el token para `TELEGRAM_BOT_TOKEN`.

### 2) Preparar Google Sheets API

1. En Google Cloud Console, habilita `Google Sheets API`.
2. Crea una **Service Account** (datos de aplicacion, no OAuth de usuarios).
3. Crea una clave JSON y descargala.
4. Copia el JSON al proyecto en:

```text
credentials/google-service-account.json
```

### 3) Crear y compartir la hoja

1. Crea una hoja de calculo en Google Sheets.
2. Copia su ID desde la URL (entre `/d/` y `/edit`).
3. Comparte la hoja con el `client_email` del JSON (`...iam.gserviceaccount.com`) como **Editor**.

### 4) Configurar variables de entorno

1. Crea `.env` desde la plantilla:

```bash
cp .env.example .env
```

2. Llena valores reales en `.env`:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
ALLOWED_CHAT_ID=tu_chat_id
GOOGLE_SHEETS_ID=tu_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
TIMEZONE=America/Mexico_City
DEFAULT_CURRENCY=MXN
SHEETS_WORKSHEET=expenses
```

Notas:
- `ALLOWED_CHAT_ID`: solo ese chat puede usar el bot.
- `GOOGLE_SHEETS_ID`: ID de la hoja, no la URL completa.
- `SHEETS_WORKSHEET`: si no existe, el bot la crea.

### 5) Levantar el bot con Docker

```bash
docker compose up -d --build
docker compose logs -f financebot
```

Si todo va bien, veras logs del polling y del proceso de mensajes.

## Uso del bot en Telegram

### Formato de gasto

Envia mensajes en formato:

```text
Descripcion monto
```

Ejemplos:
- `Uber 200`
- `Cafe 45.50`
- `Super 320,90`

Reglas:
- el monto debe ser mayor que 0,
- acepta `.` o `,` como decimal,
- si no hay regla que coincida, usa categoria `otros`.

### Comandos disponibles

- `/start` o `/help`: ayuda general
- `/cats`: lista categorias
- `/rules`: lista reglas activas
- `/addrule <palabra> <categoria>`: agrega/actualiza regla
- `/delrule <palabra>`: elimina regla
- `/last`: muestra ultimo gasto guardado

Ejemplo:

```text
/addrule uber transporte
```

## Personalizacion de categorias y reglas

- Categorias base: `config/categories.yml`
- Reglas iniciales: `config/rules.yml`

Tambien puedes manejar reglas desde Telegram con `/addrule` y `/delrule`.

## Ejecutar tests (sin Docker)

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

## Operacion diaria

- Ver estado: `docker compose ps`
- Ver logs: `docker compose logs -f financebot`
- Reiniciar: `docker compose restart financebot`
- Actualizar codigo: `git pull && docker compose up -d --build`

## Troubleshooting rapido

- `No autorizado.`
  - revisa `ALLOWED_CHAT_ID`.
- `No pude guardar en Google Sheets...`
  - revisa `GOOGLE_SHEETS_ID`.
  - revisa que la hoja este compartida con el `client_email` de la cuenta de servicio.
  - valida ruta de `GOOGLE_SERVICE_ACCOUNT_FILE`.
- El bot no arranca en Docker
  - revisa `.env` y logs con `docker compose logs -f financebot`.

## Seguridad

- No subas `.env` ni `credentials/` al repo.
- Si un token se expone, rotalo en BotFather inmediatamente.
