# FinanceBot (Telegram + Google Sheets)

Bot personal de finanzas en Python para registrar gastos desde Telegram y guardarlos en Google Sheets.

Cuando envias un mensaje como `Uber 200`, el bot:
- interpreta descripcion y monto,
- asigna categoria automaticamente con flujo hibrido (reglas -> OpenRouter -> `otros`),
- guarda una fila en Google Sheets con fecha/hora del mensaje,
- mantiene una hoja de dashboard con tablas y graficas.

## Que guarda en Google Sheets

### Hoja 1: gastos (`SHEETS_WORKSHEET`)

Columnas generadas automaticamente:
- `timestamp_utc`
- `timestamp_local`
- `descripcion`
- `monto`
- `categoria`
- `moneda`
- `telegram_message_id`

`timestamp_utc` y `timestamp_local` salen del timestamp real del mensaje de Telegram (`message.date`).

### Hoja 2: dashboard (`SHEETS_DASHBOARD_WORKSHEET`)

Se crea/actualiza automaticamente una segunda hoja con:
- tabla de gasto total por categoria,
- tabla de tendencia mensual,
- grafica de pastel: **Gasto por categoria**,
- grafica de columnas: **Tendencia mensual**.

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
SHEETS_DASHBOARD_WORKSHEET=dashboard

# OpenRouter (opcional)
OPENROUTER_API_KEY=
OPENROUTER_API_KEY_FILE=
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_TIMEOUT_SECONDS=15
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_SITE_URL=
OPENROUTER_APP_NAME=financebot
```

Notas:
- `ALLOWED_CHAT_ID`: solo ese chat puede usar el bot.
- `GOOGLE_SHEETS_ID`: ID de la hoja, no la URL completa.
- `SHEETS_WORKSHEET`: si no existe, el bot la crea.
- `SHEETS_DASHBOARD_WORKSHEET`: hoja separada para resumen y graficas.
- `OPENROUTER_API_KEY` y `OPENROUTER_API_KEY_FILE` son excluyentes; si defines ambos, se usa `OPENROUTER_API_KEY`.
- Si no defines API key de OpenRouter, la categorizacion queda solo por reglas y fallback a `otros`.

### 4.1) Recomendado en servidor: usar archivo secreto, no `.env`

Si no quieres exponer tu API key en `.env`, crea un archivo de secreto fuera del repo:

```bash
mkdir -p /run/secrets
printf '%s' 'sk-or-...' > /run/secrets/openrouter_api_key
chmod 600 /run/secrets/openrouter_api_key
```

Y configura solo:

```env
OPENROUTER_API_KEY_FILE=/run/secrets/openrouter_api_key
```

El bot no imprime la clave en logs ni en respuestas de error.

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
- si no hay regla que coincida y OpenRouter esta configurado, intenta categorizar por IA,
- si OpenRouter no esta configurado o falla, usa categoria `otros`.

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

## Categorizacion por OpenRouter

Flujo de decision:
1. Busca coincidencia por palabra clave en reglas locales.
2. Si no hay match, consulta OpenRouter con la descripcion y las categorias permitidas.
3. Si la respuesta no es valida o hay error de red/API, usa `otros`.

Esto evita depender 100% de IA y mantiene comportamiento robusto ante fallas.

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
- No se aplica categorizacion por IA
  - valida `OPENROUTER_API_KEY` o `OPENROUTER_API_KEY_FILE`.
  - valida conectividad saliente a `openrouter.ai`.
- No aparecen graficas
  - confirma que la cuenta de servicio tenga permisos de edicion en el spreadsheet.
  - revisa que exista la hoja `SHEETS_DASHBOARD_WORKSHEET`.

## Seguridad

- No subas `.env` ni `credentials/` al repo.
- Para OpenRouter en servidores, prefiere `OPENROUTER_API_KEY_FILE` con secretos montados fuera del repositorio.
- Si un token se expone, rotalo en BotFather inmediatamente.
