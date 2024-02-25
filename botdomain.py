from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, Filters
import requests
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен, полученный от BotFather
TELEGRAM_TOKEN = 'your_telegram_bot_token_here'
# Ваш API ключ для WhoisXML
WHOISXML_API_KEY = 'your_token_here'

# Хранилище языка для каждого пользователя
user_language = {}

# Локализация
localization = {
    'en': {
        'domain': "Domain",
        'status': "Status",
        'creation_date': "Creation Date",
        'expiration_date': "Expiration Date",
        'registrar': "Registrar",
        'not_found': "Sorry, domain information not found.",
        'language_set': "Language set to English.",
        'choose_language': "Please, choose one of the available languages: en, sk, ru."
    },
    'sk': {
        'domain': "Doména",
        'status': "Stav",
        'creation_date': "Dátum vytvorenia",
        'expiration_date': "Dátum expirácie",
        'registrar': "Registrátor",
        'not_found': "Ľutujeme, informácie o doméne sa nenašli.",
        'language_set': "Jazyk nastavený na slovenčinu.",
        'choose_language': "Prosím, vyberte jeden z dostupných jazykov: en, sk, ru."
    },
    'ru': {
        'domain': "Домен",
        'status': "Статус",
        'creation_date': "Дата создания",
        'expiration_date': "Дата окончания",
        'registrar': "Регистратор",
        'not_found': "Извините, информация о домене не найдена.",
        'language_set': "Язык установлен на русский.",
        'choose_language': "Пожалуйста, выберите один из доступных языков: en, sk, ru."
    }
}

def start(update: Update, context: CallbackContext) -> None:
    """Отправляет сообщение при команде /start и предлагает выбрать язык."""
    send_language_selection(update, context)

def send_language_selection(update: Update, context: CallbackContext) -> None:
    """Отправляет меню выбора языка."""
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data='language:en'),
            InlineKeyboardButton("Русский", callback_data='language:ru'),
            InlineKeyboardButton("Slovenčina", callback_data='language:sk'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose your language / Пожалуйста, выберите ваш язык / Prosím, vyberte váš jazyk:", reply_markup=reply_markup)

def language_callback(update: Update, context: CallbackContext) -> None:
    """Обрабатывает выбор языка."""
    query = update.callback_query
    query.answer()
    language = query.data.split(':')[1]
    user_language[query.from_user.id] = language

    loc = localization[language]
    query.edit_message_text(text=loc['language_set'])

def domain_info(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = update.message.text.strip()
    language = user_language.get(user.id, 'ru')  # Задаем язык по умолчанию на русский, если не указано иначе
    loc = localization[language]  # Выбираем локализацию на основе выбранного языка

    # URL для WhoisXML API
    url = f"https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={WHOISXML_API_KEY}&domainName={message}&outputFormat=JSON"

    response = requests.get(url)
    domain_data = response.json()

    if 'WhoisRecord' in domain_data:
        info = domain_data['WhoisRecord']
        registrant_info = info.get('registrant', {})
        admin_contact = info.get('administrativeContact', {})
        tech_contact = info.get('technicalContact', {})
        name_servers = info.get('nameServers', {}).get('hostNames', [])

        reply_text = f"{loc['domain']}: {info.get('domainName', 'N/A')}\n" \
                     f"{loc['status']}: {', '.join(info.get('status', [])) if info.get('status') else 'N/A'}\n" \
                     f"{loc['creation_date']}: {info.get('createdDateNormalized', 'N/A')}\n" \
                     f"{loc['expiration_date']}: {info.get('expiresDateNormalized', 'N/A')}\n" \
                     f"{loc['registrar']}: {info.get('registrarName', 'N/A')}\n\n" \
                     "Registrant Organization: {}\n" \
                     "Registrant Country: {}\n\n" \
                     "Administrative Contact Organization: {}\n" \
                     "Administrative Contact Country: {}\n\n" \
                     "Technical Contact Organization: {}\n" \
                     "Technical Contact Country: {}\n\n" \
                     "Name Servers: {}\n".format(
                         registrant_info.get('organization', 'N/A'),
                         registrant_info.get('country', 'N/A'),
                         admin_contact.get('organization', 'N/A'),
                         admin_contact.get('country', 'N/A'),
                         tech_contact.get('organization', 'N/A'),
                         tech_contact.get('country', 'N/A'),
                         ', '.join(name_servers) if name_servers else 'N/A'
                     )
    else:
        reply_text = loc['not_found']

    update.message.reply_text(reply_text)


def main() -> None:
    """Запуск бота."""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(language_callback, pattern='^language:'))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, domain_info))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
