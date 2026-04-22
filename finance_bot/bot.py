from __future__ import annotations

import telebot
from telebot.types import Message

from finance_bot.categorizer import RuleCategorizer
from finance_bot.config import Settings, load_categories, load_rules, save_rules
from finance_bot.models import ExpenseRecord
from finance_bot.openrouter_client import OpenRouterClient
from finance_bot.parser import ParseExpenseError, parse_expense_text
from finance_bot.sheets_client import SheetsClientError, SheetsExpenseWriter
from finance_bot.validators import build_timestamps, is_allowed_chat, normalize_category, normalize_keyword


class FinanceBotApp:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.categories = load_categories(settings.categories_file)
        ai_categorizer = self._build_ai_categorizer()
        self.categorizer = RuleCategorizer(load_rules(settings.rules_file), default_category="otros")
        self.categorizer.ai_categorizer = ai_categorizer
        self.categorizer.ai_categories = sorted(set(self.categories))
        self.writer = SheetsExpenseWriter(
            spreadsheet_id=settings.google_sheets_id,
            service_account_file=settings.google_service_account_file,
            worksheet_name=settings.sheets_worksheet,
            dashboard_worksheet_name=settings.sheets_dashboard_worksheet,
        )
        self.last_record: ExpenseRecord | None = None

        self.bot = telebot.TeleBot(settings.telegram_bot_token)
        self._register_handlers()

    def run(self) -> None:
        self.bot.infinity_polling(skip_pending=True)

    def _register_handlers(self) -> None:
        @self.bot.message_handler(commands=["start", "help"])
        def help_handler(message: Message) -> None:
            if not self._authorize(message):
                return
            self.bot.reply_to(message, self._help_text())

        @self.bot.message_handler(commands=["cats"])
        def categories_handler(message: Message) -> None:
            if not self._authorize(message):
                return
            formatted = "\n".join(f"- {category}" for category in sorted(self.categories))
            self.bot.reply_to(message, f"Categorias disponibles:\n{formatted}")

        @self.bot.message_handler(commands=["rules"])
        def rules_handler(message: Message) -> None:
            if not self._authorize(message):
                return
            if not self.categorizer.rules:
                self.bot.reply_to(message, "No hay reglas configuradas.")
                return

            lines = [f"- {keyword} -> {category}" for keyword, category in sorted(self.categorizer.rules.items())]
            self.bot.reply_to(message, "Reglas activas:\n" + "\n".join(lines))

        @self.bot.message_handler(commands=["addrule"])
        def add_rule_handler(message: Message) -> None:
            if not self._authorize(message):
                return

            args = message.text.split(maxsplit=2)
            if len(args) != 3:
                self.bot.reply_to(message, "Uso: /addrule <palabra> <categoria>")
                return

            keyword = normalize_keyword(args[1])
            category = normalize_category(args[2])

            if category not in self.categories:
                self.bot.reply_to(message, "Categoria invalida. Revisa /cats")
                return

            self.categorizer.add_rule(keyword, category)
            save_rules(self.settings.rules_file, self.categorizer.rules)
            self.bot.reply_to(message, f"Regla guardada: {keyword} -> {category}")

        @self.bot.message_handler(commands=["delrule"])
        def delete_rule_handler(message: Message) -> None:
            if not self._authorize(message):
                return

            args = message.text.split(maxsplit=1)
            if len(args) != 2:
                self.bot.reply_to(message, "Uso: /delrule <palabra>")
                return

            keyword = normalize_keyword(args[1])
            deleted = self.categorizer.delete_rule(keyword)
            if not deleted:
                self.bot.reply_to(message, f"No existe la regla para: {keyword}")
                return

            save_rules(self.settings.rules_file, self.categorizer.rules)
            self.bot.reply_to(message, f"Regla eliminada: {keyword}")

        @self.bot.message_handler(commands=["last"])
        def last_handler(message: Message) -> None:
            if not self._authorize(message):
                return

            if self.last_record is None:
                self.bot.reply_to(message, "Aun no hay gastos registrados en esta sesion.")
                return

            last = self.last_record
            response = (
                "Ultimo gasto:\n"
                f"- {last.description}\n"
                f"- Monto: {format(last.amount, 'f')} {last.currency}\n"
                f"- Categoria: {last.category}\n"
                f"- Fecha local: {last.timestamp_local.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.bot.reply_to(message, response)

        @self.bot.message_handler(func=self._should_process_as_expense)
        def expense_handler(message: Message) -> None:
            if not self._authorize(message):
                return

            try:
                description, amount = parse_expense_text(message.text or "")
                category = self.categorizer.categorize(description)
                timestamp_utc, timestamp_local = build_timestamps(message.date, self.settings.timezone)

                record = ExpenseRecord(
                    description=description,
                    amount=amount,
                    category=category,
                    currency=self.settings.default_currency,
                    timestamp_utc=timestamp_utc,
                    timestamp_local=timestamp_local,
                    telegram_message_id=message.message_id,
                )

                self.writer.append_expense(record)
                self.last_record = record

                self.bot.reply_to(
                    message,
                    (
                        "Gasto registrado\n"
                        f"- {record.description}\n"
                        f"- {format(record.amount, 'f')} {record.currency}\n"
                        f"- Categoria: {record.category}\n"
                        f"- Fecha: {record.timestamp_local.strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                )
            except ParseExpenseError as error:
                self.bot.reply_to(message, str(error))
            except SheetsClientError as error:
                self.bot.reply_to(message, f"No pude guardar en Google Sheets: {error}")
            except Exception as error:  # noqa: BLE001
                self.bot.reply_to(message, f"Error inesperado al guardar el gasto: {error}")

    def _authorize(self, message: Message) -> bool:
        allowed = is_allowed_chat(message.chat.id, self.settings.allowed_chat_id)
        if not allowed:
            self.bot.reply_to(message, "No autorizado.")
        return allowed

    @staticmethod
    def _should_process_as_expense(message: Message) -> bool:
        text = (message.text or "").strip()
        if not text:
            return False
        return not text.startswith("/")

    def _build_ai_categorizer(self) -> OpenRouterClient | None:
        if not self.settings.openrouter_api_key:
            return None

        return OpenRouterClient(
            api_key=self.settings.openrouter_api_key,
            model=self.settings.openrouter_model,
            timeout_seconds=self.settings.openrouter_timeout_seconds,
            base_url=self.settings.openrouter_base_url,
            site_url=self.settings.openrouter_site_url,
            app_name=self.settings.openrouter_app_name,
        )

    @staticmethod
    def _help_text() -> str:
        return (
            "Bot personal de finanzas\n\n"
            "Formato de gasto:\n"
            "- Descripcion monto\n"
            "- Ejemplo: Uber 200\n\n"
            "Comandos:\n"
            "- /cats\n"
            "- /rules\n"
            "- /addrule <palabra> <categoria>\n"
            "- /delrule <palabra>\n"
            "- /last"
        )
