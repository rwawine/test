"""
Support handlers for the Telegram bot
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from models import SupportStates
from keyboards import *
from database import DatabaseManager

logger = logging.getLogger(__name__)

def create_support_router(db_manager: DatabaseManager) -> Router:
    """Create support system router"""
    router = Router()
    
    @router.message(F.text == "💬 Техподдержка")
    async def support_menu(message: Message, state: FSMContext):
        """Show support menu"""
        await state.clear()
        
        await message.answer(
            "💬 Центр поддержки\n\n"
            "Выберите, что вас интересует:\n\n"
            "❓ Частые вопросы - быстрые ответы на популярные вопросы\n"
            "📝 Написать сообщение - создать обращение в поддержку\n"
            "📞 Мои обращения - проверить статус ваших обращений",
            reply_markup=get_support_menu_keyboard()
        )
    
    @router.message(F.text == "❓ Частые вопросы")
    async def show_faq(message: Message):
        """Show FAQ menu"""
        await message.answer(
            "❓ Частые вопросы\n\n"
            "Выберите интересующую вас тему:",
            reply_markup=get_faq_keyboard()
        )
    
    @router.callback_query(F.data == "faq_registration")
    async def faq_registration(callback: CallbackQuery):
        """FAQ: Registration process"""
        faq_text = (
            "📋 Как подать заявку на участие?\n\n"
            "1️⃣ Нажмите кнопку '🚀 Начать регистрацию'\n"
            "2️⃣ Введите ваше полное имя\n"
            "3️⃣ Укажите номер телефона\n"
            "4️⃣ Введите номер карты лояльности\n"
            "5️⃣ Загрузите фото рекламного лифлета\n"
            "6️⃣ Подтвердите данные\n\n"
            "⏱️ Рассмотрение заявки занимает 1-2 рабочих дня.\n"
            "📧 Уведомление о статусе придет в этот чат."
        )
        
        await callback.message.edit_text(faq_text)
    
    @router.callback_query(F.data == "faq_results")
    async def faq_results(callback: CallbackQuery):
        """FAQ: Results timing"""
        faq_text = (
            "🕐 Когда будут результаты розыгрыша?\n\n"
            "📅 Розыгрыш состоится: 5 ноября 2024\n"
            "🕐 Время: 15:00 МСК\n"
            "📺 Прямая трансляция в официальном канале\n\n"
            "📢 Результаты будут объявлены:\n"
            "• Сразу после розыгрыша\n"
            "• Уведомления всем участникам\n"
            "• Публикация в социальных сетях\n\n"
            "🏆 Связь с победителями в течение 3 рабочих дней"
        )
        
        await callback.message.edit_text(faq_text)
    
    @router.callback_query(F.data == "faq_prizes")
    async def faq_prizes(callback: CallbackQuery):
        """FAQ: Prize information"""
        faq_text = (
            "🏆 Призы розыгрыша\n\n"
            "🥇 Главный приз: Сертификат 50 000 ₽\n"
            "🥈 5 призов по 10 000 ₽\n"
            "🥉 10 призов по 5 000 ₽\n"
            "🎁 20 призов по 1 000 ₽\n"
            "💳 100 промокодов на скидку 20%\n\n"
            "📋 Получение призов:\n"
            "• В течение 30 дней после розыгрыша\n"
            "• При предъявлении документов\n"
            "• Сертификаты действительны 6 месяцев"
        )
        
        await callback.message.edit_text(faq_text)
    
    @router.callback_query(F.data == "faq_photo")
    async def faq_photo(callback: CallbackQuery):
        """FAQ: Photo problems"""
        faq_text = (
            "📱 Проблемы с загрузкой фото\n\n"
            "✅ Требования к фото:\n"
            "• Формат: JPG, PNG, GIF\n"
            "• Размер: до 10 МБ\n"
            "• Четкое изображение лифлета\n"
            "• Хорошее освещение\n\n"
            "❌ Частые проблемы:\n"
            "• Слишком большой размер файла\n"
            "• Неподдерживаемый формат\n"
            "• Размытое или темное фото\n\n"
            "💡 Советы:\n"
            "• Сфотографируйте лифлет при хорошем свете\n"
            "• Держите камеру ровно\n"
            "• Убедитесь, что весь лифлет в кадре"
        )
        
        await callback.message.edit_text(faq_text)
    
    @router.callback_query(F.data == "faq_cards")
    async def faq_cards(callback: CallbackQuery):
        """FAQ: Loyalty cards"""
        faq_text = (
            "💳 Вопросы по картам лояльности\n\n"
            "🔍 Где найти номер карты?\n"
            "• В мобильном приложении\n"
            "• На физической карте\n"
            "• В SMS при регистрации\n"
            "• В личном кабинете на сайте\n\n"
            "📝 Формат номера:\n"
            "• От 8 до 16 цифр\n"
            "• Только цифры, без букв\n\n"
            "❗️ Важно:\n"
            "• Одна карта = одна заявка\n"
            "• Карта должна быть активной\n"
            "• Проверьте правильность ввода"
        )
        
        await callback.message.edit_text(faq_text)
    
    @router.callback_query(F.data.in_(["create_ticket", "faq_other"]))
    async def start_ticket_creation(callback: CallbackQuery, state: FSMContext):
        """Start creating support ticket"""
        await state.set_state(SupportStates.WAITING_CATEGORY)
        
        await callback.message.edit_text(
            "📝 Создание обращения в техподдержку\n\n"
            "Выберите категорию вашего вопроса:"
        )
        
        await callback.message.answer(
            "Категории проблем:",
            reply_markup=get_support_categories_keyboard()
        )
    
    @router.message(F.text == "📝 Написать сообщение")
    async def create_ticket_message(message: Message, state: FSMContext):
        """Create ticket from message"""
        await state.set_state(SupportStates.WAITING_CATEGORY)
        
        await message.answer(
            "📝 Создание обращения в техподдержку\n\n"
            "Выберите категорию вашего вопроса:",
            reply_markup=get_support_categories_keyboard()
        )
    
    @router.callback_query(F.data.startswith("cat_"), StateFilter(SupportStates.WAITING_CATEGORY))
    async def select_category(callback: CallbackQuery, state: FSMContext):
        """Select support category"""
        category_map = {
            'cat_photo': 'Проблема с фото',
            'cat_card': 'Вопрос по карте лояльности',
            'cat_tech': 'Технические проблемы',
            'cat_status': 'Статус заявки',
            'cat_lottery': 'Вопросы о розыгрыше',
            'cat_other': 'Другая проблема'
        }
        
        category = category_map.get(callback.data, 'Другая проблема')
        await state.update_data(category=category)
        await state.set_state(SupportStates.WAITING_DESCRIPTION)
        
        await callback.message.edit_text(
            f"📝 Категория: {category}\n\n"
            "Опишите вашу проблему подробно:"
        )
        
        await callback.message.answer(
            "✍️ Напишите подробное описание вашего вопроса или проблемы:",
            reply_markup=get_ticket_actions_keyboard()
        )
    
    @router.message(StateFilter(SupportStates.WAITING_DESCRIPTION))
    async def process_description(message: Message, state: FSMContext):
        """Process ticket description"""
        if message.text in ["📷 Прикрепить фото", "📄 Прикрепить документ"]:
            await state.set_state(SupportStates.WAITING_ATTACHMENT)
            await message.answer(
                "📎 Прикрепите файл к обращению\n\n"
                "Вы можете прикрепить:\n"
                "• Фотографию (JPG, PNG, GIF)\n"
                "• Документ\n"
                "• Скриншот проблемы\n\n"
                "Или нажмите '✅ Отправить обращение' если файл не нужен."
            )
            return
        
        if message.text == "✅ Отправить обращение":
            await self._create_ticket(message, state)
            return
        
        if message.text == "⬅️ Изменить категорию":
            await state.set_state(SupportStates.WAITING_CATEGORY)
            await message.answer(
                "Выберите категорию:",
                reply_markup=get_support_categories_keyboard()
            )
            return
        
        if message.text == "🏠 Главное меню":
            await state.clear()
            await message.answer(
                "Создание обращения отменено.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Save description
        await state.update_data(description=message.text)
        
        data = await state.get_data()
        await message.answer(
            f"✅ Описание сохранено!\n\n"
            f"📝 Категория: {data.get('category', 'Не выбрана')}\n"
            f"📄 Описание: {message.text[:100]}{'...' if len(message.text) > 100 else ''}\n\n"
            f"Хотите прикрепить файл или отправить обращение?",
            reply_markup=get_ticket_actions_keyboard()
        )
    
    @router.message(F.photo, StateFilter(SupportStates.WAITING_ATTACHMENT))
    async def process_attachment_photo(message: Message, state: FSMContext):
        """Process photo attachment"""
        try:
            from utils.file_handler import save_photo
            
            # Save photo
            photo_path = await save_photo(message.bot, message.photo[-1].file_id, message.from_user.id)
            
            if photo_path:
                await state.update_data(attachment_path=photo_path)
                await message.answer(
                    "✅ Фото прикреплено к обращению!\n\n"
                    "Готовы отправить обращение?",
                    reply_markup=get_ticket_actions_keyboard()
                )
            else:
                await message.answer(
                    "❌ Ошибка при сохранении фото. Попробуйте еще раз.",
                    reply_markup=get_ticket_actions_keyboard()
                )
        except Exception as e:
            await message.answer(
                "❌ Ошибка при обработке фото. Попробуйте еще раз.",
                reply_markup=get_ticket_actions_keyboard()
            )
    
    @router.message(F.text == "✅ Отправить обращение", StateFilter(SupportStates.WAITING_DESCRIPTION, SupportStates.WAITING_ATTACHMENT))
    async def create_ticket(message: Message, state: FSMContext):
        """Create support ticket"""
        await self._create_ticket(message, state)
    
    async def _create_ticket(self, message: Message, state: FSMContext):
        """Internal method to create ticket"""
        data = await state.get_data()
        
        if not data.get('description'):
            await message.answer(
                "❌ Описание проблемы обязательно!\n\n"
                "Пожалуйста, опишите вашу проблему:",
                reply_markup=get_ticket_actions_keyboard()
            )
            return
        
        try:
            # Get participant info
            participant = db_manager.get_participant_by_telegram_id(message.from_user.id)
            
            # Create ticket
            ticket_id = db_manager.create_support_ticket(
                user_id=message.from_user.id,
                username=message.from_user.username or "",
                subject=data.get('category', 'Обращение в поддержку'),
                participant_id=participant['id'] if participant else None
            )
            
            # Add initial message
            db_manager.add_support_message(
                ticket_id=ticket_id,
                sender_id=message.from_user.id,
                sender_type='user',
                message_text=data['description'],
                attachment_path=data.get('attachment_path')
            )
            
            # Get ticket number for user
            conn = db_manager.connect()
            ticket_info = conn.execute("""
                SELECT ticket_number FROM support_tickets WHERE id = ?
            """, [ticket_id]).fetchone()
            
            ticket_number = ticket_info[0] if ticket_info else "Unknown"
            
            await state.clear()
            
            await message.answer(
                f"✅ Обращение создано успешно!\n\n"
                f"🎫 Номер обращения: {ticket_number}\n"
                f"📝 Категория: {data.get('category')}\n"
                f"⏱️ Статус: На рассмотрении\n\n"
                f"📧 Ответ придет в этот чат в течение 24 часов.\n"
                f"💬 Вы можете проверить статус в разделе 'Мои обращения'.",
                reply_markup=get_main_menu_keyboard()
            )
            
            # TODO: Notify admins about new ticket
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await message.answer(
                "❌ Ошибка при создании обращения. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
    
    @router.message(F.text == "📞 Мои обращения")
    async def my_tickets(message: Message):
        """Show user's tickets"""
        conn = db_manager.connect()
        
        tickets = conn.execute("""
            SELECT ticket_number, subject, status, created_at
            FROM support_tickets 
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, [message.from_user.id]).fetchall()
        
        if not tickets:
            await message.answer(
                "📭 У вас пока нет обращений в техподдержку.\n\n"
                "Вы можете создать обращение, нажав '📝 Написать сообщение'.",
                reply_markup=get_support_menu_keyboard()
            )
            return
        
        tickets_text = "📞 Ваши обращения:\n\n"
        
        for ticket in tickets:
            status_emoji = {
                'open': '🟡',
                'in_progress': '🔵',
                'closed': '🟢'
            }.get(ticket[2], '⚪')
            
            status_text = {
                'open': 'Открыто',
                'in_progress': 'В работе',
                'closed': 'Закрыто'
            }.get(ticket[2], 'Неизвестно')
            
            tickets_text += (
                f"{status_emoji} {ticket[0]}\n"
                f"📝 {ticket[1]}\n"
                f"📅 {ticket[3]}\n"
                f"Status: {status_text}\n\n"
            )
        
        await message.answer(
            tickets_text,
            reply_markup=get_support_menu_keyboard()
        )
    
    return router