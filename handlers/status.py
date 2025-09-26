"""
Status and general handlers
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards import *
from database import DatabaseManager

def create_status_router(db_manager: DatabaseManager) -> Router:
    """Create status checking router"""
    router = Router()
    
    @router.message(F.text == "📋 Мой статус")
    async def check_status(message: Message):
        """Check user registration status"""
        participant = db_manager.get_participant_by_telegram_id(message.from_user.id)
        
        if not participant:
            await message.answer(
                "❌ Вы еще не зарегистрированы в розыгрыше!\n\n"
                "Нажмите '🚀 Начать регистрацию' для участия.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        status_text = {
            'pending': '⏳ На рассмотрении',
            'approved': '✅ Одобрена', 
            'rejected': '❌ Отклонена'
        }.get(participant['status'], participant['status'])
        
        status_description = {
            'pending': 'Ваша заявка рассматривается администратором. Ожидайте уведомления.',
            'approved': 'Поздравляем! Вы участвуете в розыгрыше. Следите за объявлением результатов.',
            'rejected': 'К сожалению, ваша заявка была отклонена. Обратитесь в техподдержку для уточнения причин.'
        }.get(participant['status'], '')
        
        response_text = (
            f"📋 Статус вашей заявки: {status_text}\n\n"
            f"👤 Имя: {participant['full_name']}\n"
            f"📞 Телефон: {participant['phone_number']}\n"
            f"💳 Карта лояльности: {participant['loyalty_card']}\n"
            f"📅 Дата регистрации: {participant['registration_date']}\n\n"
            f"{status_description}"
        )
        
        if participant['admin_notes']:
            response_text += f"\n\n📝 Комментарий администратора:\n{participant['admin_notes']}"
        
        await message.answer(
            response_text,
            reply_markup=get_status_keyboard()
        )
    
    @router.message(F.text == "🔄 Обновить статус")
    async def refresh_status(message: Message):
        """Refresh status - same as check status"""
        await check_status(message)
    
    @router.message(F.text == "📊 О розыгрыше")
    async def about_lottery(message: Message):
        """Show lottery information"""
        # Get basic statistics
        stats = db_manager.get_statistics()
        
        info_text = (
            "🎉 О нашем розыгрыше\n\n"
            f"👥 Всего участников: {stats.get('total_participants', 0)}\n"
            f"🏆 Уже выиграли: {stats.get('total_winners', 0)}\n\n"
            "ℹ️ Выберите раздел для подробной информации:"
        )
        
        await message.answer(
            info_text,
            reply_markup=get_info_menu_keyboard()
        )
    
    @router.callback_query(F.data == "info_rules")
    async def show_rules(callback: CallbackQuery):
        """Show participation rules"""
        rules_text = (
            "📋 Правила участия в розыгрыше\n\n"
            "✅ Кто может участвовать:\n"
            "• Совершеннолетние граждане РФ\n"
            "• Владельцы карт лояльности\n"
            "• Один участник = одна заявка\n\n"
            "📝 Для участия необходимо:\n"
            "1️⃣ Указать настоящие данные\n"
            "2️⃣ Предоставить действующий номер телефона\n"
            "3️⃣ Загрузить фото рекламного лифлета\n"
            "4️⃣ Дождаться одобрения заявки\n\n"
            "⚠️ Важно:\n"
            "• Заявки с недостоверными данными отклоняются\n"
            "• Один телефон/карта = одна заявка\n"
            "• Решение администрации окончательно"
        )
        
        await callback.message.edit_text(rules_text)
    
    @router.callback_query(F.data == "info_prizes")
    async def show_prizes(callback: CallbackQuery):
        """Show prizes information"""
        prizes_text = (
            "🏆 Призы розыгрыша\n\n"
            "🥇 Главный приз:\n"
            "• Сертификат на 50 000 ₽\n\n"
            "🥈 Дополнительные призы:\n"
            "• 5 сертификатов по 10 000 ₽\n"
            "• 10 сертификатов по 5 000 ₽\n"
            "• 20 сертификатов по 1 000 ₽\n\n"
            "🎁 Поощрительные призы:\n"
            "• 100 промокодов на скидку 20%\n\n"
            "📋 Условия получения:\n"
            "• Получение в течение 30 дней\n"
            "• При предъявлении документов\n"
            "• Сертификаты действительны 6 месяцев"
        )
        
        await callback.message.edit_text(prizes_text)
    
    @router.callback_query(F.data == "info_dates")
    async def show_dates(callback: CallbackQuery):
        """Show important dates"""
        dates_text = (
            "📅 Важные даты розыгрыша\n\n"
            "📝 Прием заявок:\n"
            "• Начало: 1 октября 2024\n"
            "• Окончание: 31 октября 2024\n\n"
            "🎲 Розыгрыш призов:\n"
            "• Дата: 5 ноября 2024\n"
            "• Время: 15:00 МСК\n"
            "• Трансляция в официальном канале\n\n"
            "🏆 Объявление результатов:\n"
            "• Сразу после розыгрыша\n"
            "• Уведомления всем участникам\n"
            "• Публикация в социальных сетях\n\n"
            "📞 Связь с победителями:\n"
            "• В течение 3 рабочих дней\n"
            "• По указанному телефону"
        )
        
        await callback.message.edit_text(dates_text)
    
    @router.callback_query(F.data == "info_fairness")
    async def show_fairness(callback: CallbackQuery):
        """Show fairness guarantees"""
        fairness_text = (
            "⚖️ Гарантии честности розыгрыша\n\n"
            "🔒 Технические гарантии:\n"
            "• Криптографически стойкий генератор случайных чисел\n"
            "• Публичный хеш для проверки честности\n"
            "• Невозможность предсказания результата\n\n"
            "👥 Общественный контроль:\n"
            "• Прямая трансляция розыгрыша\n"
            "• Присутствие независимых наблюдателей\n"
            "• Видеозапись всего процесса\n\n"
            "📊 Прозрачность:\n"
            "• Публикация алгоритма розыгрыша\n"
            "• Возможность проверки результатов\n"
            "• Открытая статистика участников\n\n"
            "📞 Обратная связь:\n"
            "• Техподдержка для всех вопросов\n"
            "• Рассмотрение жалоб и предложений"
        )
        
        await callback.message.edit_text(fairness_text)
    
    @router.callback_query(F.data == "info_contacts")
    async def show_contacts(callback: CallbackQuery):
        """Show organizer contacts"""
        contacts_text = (
            "📞 Контакты организаторов\n\n"
            "🏢 Организатор:\n"
            "ООО 'Торговая сеть'\n\n"
            "📍 Адрес:\n"
            "г. Москва, ул. Примерная, д. 123\n\n"
            "☎️ Телефон горячей линии:\n"
            "+7 (800) 123-45-67\n"
            "(звонок бесплатный)\n\n"
            "📧 Email:\n"
            "lottery@example.com\n\n"
            "🕐 Часы работы:\n"
            "Пн-Пт: 9:00 - 18:00 МСК\n"
            "Сб-Вс: выходные\n\n"
            "💬 Техподдержка в боте:\n"
            "Используйте кнопку 'Техподдержка'\n"
            "в главном меню"
        )
        
        await callback.message.edit_text(contacts_text)
    
    @router.message(F.text == "❓ Помощь")
    async def show_help(message: Message):
        """Show general help"""
        help_text = (
            "❓ Справка по использованию бота\n\n"
            "🚀 Как участвовать:\n"
            "1. Нажмите 'Начать регистрацию'\n"
            "2. Заполните все данные\n"
            "3. Дождитесь одобрения заявки\n"
            "4. Участвуйте в розыгрыше!\n\n"
            "📋 Полезные кнопки:\n"
            "• 'Мой статус' - проверить заявку\n"
            "• 'О розыгрыше' - подробная информация\n"
            "• 'Техподдержка' - задать вопрос\n\n"
            "❗️ Проблемы?\n"
            "Обратитесь в техподдержку через соответствующую кнопку в меню."
        )
        
        await message.answer(
            help_text,
            reply_markup=get_main_menu_keyboard()
        )
    
    @router.message(F.text == "🏠 Главное меню")
    async def back_to_menu(message: Message):
        """Return to main menu"""
        await message.answer(
            "🏠 Главное меню",
            reply_markup=get_main_menu_keyboard()
        )
    
    return router