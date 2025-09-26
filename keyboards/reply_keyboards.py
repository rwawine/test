"""
Keyboard layouts for the Telegram bot
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Main menu keyboard
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [KeyboardButton(text="🚀 Начать регистрацию")],
        [KeyboardButton(text="📋 Мой статус"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="💬 Техподдержка"), KeyboardButton(text="📊 О розыгрыше")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Registration process keyboards
def get_name_input_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for name input step"""
    keyboard = [
        [KeyboardButton(text="⬅️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_phone_input_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for phone input step"""
    keyboard = [
        [KeyboardButton(text="📞 Отправить мой номер", request_contact=True)],
        [KeyboardButton(text="✏️ Ввести вручную")],
        [KeyboardButton(text="⬅️ Назад к имени")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_loyalty_card_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for loyalty card input"""
    keyboard = [
        [KeyboardButton(text="⬅️ Назад к телефону")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_photo_upload_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for photo upload step"""
    keyboard = [
        [KeyboardButton(text="📷 Сделать фото"), KeyboardButton(text="🖼️ Выбрать из галереи")],
        [KeyboardButton(text="❓ Что такое лифлет?")],
        [KeyboardButton(text="⬅️ Назад к карте лояльности")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for data confirmation"""
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_name"),
            InlineKeyboardButton(text="✏️ Изменить телефон", callback_data="edit_phone")
        ],
        [
            InlineKeyboardButton(text="✏️ Изменить карту", callback_data="edit_card"),
            InlineKeyboardButton(text="✏️ Изменить фото", callback_data="edit_photo")
        ],
        [
            InlineKeyboardButton(text="✅ Все верно, зарегистрировать", callback_data="confirm_registration")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить регистрацию", callback_data="cancel_registration")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Status check keyboards
def get_status_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for status checking"""
    keyboard = [
        [KeyboardButton(text="🔄 Обновить статус")],
        [KeyboardButton(text="💬 Написать в поддержку")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Support system keyboards
def get_support_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main support menu keyboard"""
    keyboard = [
        [KeyboardButton(text="❓ Частые вопросы")],
        [KeyboardButton(text="📝 Написать сообщение")],
        [KeyboardButton(text="📞 Мои обращения")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_faq_keyboard() -> InlineKeyboardMarkup:
    """FAQ categories keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📋 Как подать заявку?", callback_data="faq_registration")],
        [InlineKeyboardButton(text="🕐 Когда будут результаты?", callback_data="faq_results")],
        [InlineKeyboardButton(text="🏆 Что можно выиграть?", callback_data="faq_prizes")],
        [InlineKeyboardButton(text="📱 Проблемы с фото", callback_data="faq_photo")],
        [InlineKeyboardButton(text="💳 Вопросы по картам", callback_data="faq_cards")],
        [InlineKeyboardButton(text="📞 Другой вопрос", callback_data="create_ticket")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_support_categories_keyboard() -> InlineKeyboardMarkup:
    """Support ticket categories keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📷 Проблема с фото", callback_data="cat_photo")],
        [InlineKeyboardButton(text="💳 Вопрос по карте лояльности", callback_data="cat_card")],
        [InlineKeyboardButton(text="📱 Технические проблемы", callback_data="cat_tech")],
        [InlineKeyboardButton(text="📋 Статус заявки", callback_data="cat_status")],
        [InlineKeyboardButton(text="🏆 Вопросы о розыгрыше", callback_data="cat_lottery")],
        [InlineKeyboardButton(text="✏️ Другая проблема", callback_data="cat_other")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ticket_actions_keyboard() -> ReplyKeyboardMarkup:
    """Actions for ticket creation"""
    keyboard = [
        [KeyboardButton(text="📷 Прикрепить фото"), KeyboardButton(text="📄 Прикрепить документ")],
        [KeyboardButton(text="✅ Отправить обращение")],
        [KeyboardButton(text="⬅️ Изменить категорию"), KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Information keyboards
def get_info_menu_keyboard() -> InlineKeyboardMarkup:
    """Information menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📋 Правила участия", callback_data="info_rules")],
        [InlineKeyboardButton(text="🏆 Призы розыгрыша", callback_data="info_prizes")],
        [InlineKeyboardButton(text="📅 Сроки проведения", callback_data="info_dates")],
        [InlineKeyboardButton(text="⚖️ Гарантии честности", callback_data="info_fairness")],
        [InlineKeyboardButton(text="📞 Контакты организаторов", callback_data="info_contacts")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Admin keyboards (for quick actions)
def get_admin_quick_keyboard() -> ReplyKeyboardMarkup:
    """Quick admin actions keyboard"""
    keyboard = [
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📤 Быстрый экспорт")],
        [KeyboardButton(text="🎲 Провести розыгрыш"), KeyboardButton(text="📢 Создать рассылку")],
        [KeyboardButton(text="🌐 Открыть админку")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Universal action keyboards
def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    """Simple back to menu keyboard"""
    keyboard = [
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)