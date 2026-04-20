from dotenv import load_dotenv

from finance_bot.bot import FinanceBotApp
from finance_bot.config import load_settings


def main() -> None:
    load_dotenv()
    settings = load_settings()
    app = FinanceBotApp(settings)
    print("Bot iniciado...")
    app.run()


if __name__ == "__main__":
    main()
