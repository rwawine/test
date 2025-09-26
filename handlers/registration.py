"""
Main handlers for the Telegram bot
"""

import re
import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime
from pathlib import Path

from models import RegistrationStates
from keyboards import *
from utils.validators import validate_phone, validate_loyalty_card, validate_name
from utils.file_handler import save_photo
from database import DatabaseManager

logger = logging.getLogger(__name__)

def create_registration_router(db_manager: DatabaseManager) -> Router:
    """Create and configure registration router"""
    router = Router()
    
    @router.message(Command("start"))
    async def start_handler(message: Message, state: FSMContext):
        """Handle /start command"""
        await state.clear()
        
        # Check if user is already registered
        participant = db_manager.get_participant_by_telegram_id(message.from_user.id)
        
        if participant:
            status_text = {
                'pending': '⏳ На рассмотрении',
                'approved': '✅ Одобрена',
                'rejected': '❌ Отклонена'
            }.get(participant['status'], participant['status'])
            
            await message.answer(
                f"👋 Добро пожаловать, {participant['full_name']}!\n\n"
                f"Ваша заявка: {status_text}\n"
                f"Дата регистрации: {participant['registration_date']}\n\n"
                f"Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "🎉 Добро пожаловать в розыгрыш призов!\n\n"
                "🏆 Участвуйте в розыгрыше и выигрывайте ценные призы!\n\n"
                "Для участия необходимо:\n"
                "1️⃣ Указать ваше имя\n"
                "2️⃣ Предоставить номер телефона\n"
                "3️⃣ Ввести номер карты лояльности\n"
                "4️⃣ Загрузить фото лифлета\n\n"
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )
    
    @router.message(F.text == "🚀 Начать регистрацию")
    async def start_registration(message: Message, state: FSMContext):
        """Start registration process"""
        # Check if already registered
        participant = db_manager.get_participant_by_telegram_id(message.from_user.id)
        
        if participant:
            await message.answer(
                "❗️ Вы уже зарегистрированы в розыгрыше!\n\n"
                "Проверьте статус вашей заявки в разделе '📋 Мой статус'",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await state.set_state(RegistrationStates.WAITING_NAME)
        await message.answer(
            "📝 Шаг 1 из 4: Введите ваше полное имя\n\n"
            "Укажите имя и фамилию, как в документах.\n"
            "Это поможет нам связаться с вами в случае выигрыша.",
            reply_markup=get_name_input_keyboard()
        )
    
    @router.message(StateFilter(RegistrationStates.WAITING_NAME))
    async def process_name(message: Message, state: FSMContext):
        """Process name input"""
        if message.text == "⬅️ Назад в меню":
            await state.clear()
            await message.answer(
                "Регистрация отменена. Возвращаемся в главное меню.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        if not validate_name(message.text):
            await message.answer(
                "❌ Некорректное имя!\n\n"
                "Имя должно содержать только буквы и быть длиной от 2 до 50 символов.\n"
                "Пожалуйста, введите корректное имя:",
                reply_markup=get_name_input_keyboard()
            )
            return
        
        await state.update_data(full_name=message.text.strip())
        await state.set_state(RegistrationStates.WAITING_PHONE)
        
        await message.answer(
            "📞 Шаг 2 из 4: Укажите номер телефона\n\n"
            "Вы можете:\n"
            "• Нажать кнопку '📞 Отправить мой номер' для автоматической отправки\n"
            "• Или ввести номер вручную в формате +7XXXXXXXXXX",
            reply_markup=get_phone_input_keyboard()
        )
    
    @router.message(F.contact, StateFilter(RegistrationStates.WAITING_PHONE))
    async def process_contact(message: Message, state: FSMContext):
        """Process contact sharing"""
        phone = message.contact.phone_number
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Validate phone
        if not validate_phone(phone):
            await message.answer(
                "❌ Некорректный номер телефона!\n\n"
                "Номер должен быть российским (+7XXXXXXXXXX).\n"
                "Попробуйте еще раз:",
                reply_markup=get_phone_input_keyboard()
            )
            return
        
        # Check if phone already exists
        if db_manager.check_phone_exists(phone):
            await message.answer(
                "❌ Этот номер телефона уже используется!\n\n"
                "Каждый участник может зарегистрироваться только один раз.\n"
                "Если это ваш номер, проверьте статус в разделе '📋 Мой статус'",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        await state.update_data(phone_number=phone)
        await state.set_state(RegistrationStates.WAITING_LOYALTY_CARD)
        
        await message.answer(
            "💳 Шаг 3 из 4: Введите номер карты лояльности\n\n"
            "Укажите номер вашей карты лояльности (8-16 цифр).\n"
            "Карту можно найти в мобильном приложении или на физической карте.",
            reply_markup=get_loyalty_card_keyboard()
        )
    
    @router.message(F.text == "✏️ Ввести вручную", StateFilter(RegistrationStates.WAITING_PHONE))
    async def manual_phone_input(message: Message):
        """Switch to manual phone input"""
        await message.answer(
            "📝 Введите номер телефона вручную\n\n"
            "Формат: +7XXXXXXXXXX (например: +79123456789)",
            reply_markup=get_loyalty_card_keyboard()
        )
    
    @router.message(StateFilter(RegistrationStates.WAITING_PHONE))
    async def process_phone_text(message: Message, state: FSMContext):
        """Process phone number text input"""
        if message.text == "⬅️ Назад к имени":
            await state.set_state(RegistrationStates.WAITING_NAME)
            await message.answer(
                "📝 Шаг 1 из 4: Введите ваше полное имя",
                reply_markup=get_name_input_keyboard()
            )
            return
        
        phone = message.text.strip()
        
        # Add + if missing
        if not phone.startswith('+') and phone.startswith('7'):
            phone = '+' + phone
        elif not phone.startswith('+') and phone.startswith('8'):
            phone = '+7' + phone[1:]
        
        if not validate_phone(phone):
            await message.answer(
                "❌ Некорректный номер телефона!\n\n"
                "Используйте формат: +7XXXXXXXXXX\n"
                "Пример: +79123456789\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_phone_input_keyboard()
            )
            return
        
        # Check if phone exists
        if db_manager.check_phone_exists(phone):
            await message.answer(
                "❌ Этот номер телефона уже используется!\n\n"
                "Каждый участник может зарегистрироваться только один раз.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        await state.update_data(phone_number=phone)
        await state.set_state(RegistrationStates.WAITING_LOYALTY_CARD)
        
        await message.answer(
            "💳 Шаг 3 из 4: Введите номер карты лояльности\n\n"
            "Укажите номер вашей карты лояльности (8-16 цифр).",
            reply_markup=get_loyalty_card_keyboard()
        )
    
    @router.message(StateFilter(RegistrationStates.WAITING_LOYALTY_CARD))
    async def process_loyalty_card(message: Message, state: FSMContext):
        """Process loyalty card input"""
        if message.text == "⬅️ Назад к телефону":
            await state.set_state(RegistrationStates.WAITING_PHONE)
            await message.answer(
                "📞 Шаг 2 из 4: Укажите номер телефона",
                reply_markup=get_phone_input_keyboard()
            )
            return
        
        if message.text == "🏠 Главное меню":
            await state.clear()
            await message.answer(
                "Регистрация отменена.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        loyalty_card = message.text.strip()
        
        if not validate_loyalty_card(loyalty_card):
            await message.answer(
                "❌ Некорректный номер карты лояльности!\n\n"
                "Номер должен содержать от 8 до 16 цифр.\n"
                "Пример: 12345678\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_loyalty_card_keyboard()
            )
            return
        
        # Check if card exists
        if db_manager.check_loyalty_card_exists(loyalty_card):
            await message.answer(
                "❌ Эта карта лояльности уже используется!\n\n"
                "Каждая карта может быть использована только один раз.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        await state.update_data(loyalty_card=loyalty_card)
        await state.set_state(RegistrationStates.WAITING_LEAFLET_PHOTO)
        
        await message.answer(
            "📷 Шаг 4 из 4: Загрузите фото лифлета\n\n"
            "Сфотографируйте или выберите из галереи фото рекламного лифлета.\n\n"
            "❓ Лифлет - это рекламная листовка о товарах и акциях.",
            reply_markup=get_photo_upload_keyboard()
        )
    
    @router.message(F.text == "❓ Что такое лифлет?", StateFilter(RegistrationStates.WAITING_LEAFLET_PHOTO))
    async def explain_leaflet(message: Message):
        """Explain what leaflet is"""
        await message.answer(
            "📄 Что такое лифлет?\n\n"
            "Лифлет - это рекламная листовка или брошюра с информацией о:\n"
            "• Товарах и их ценах\n"
            "• Скидках и акциях\n"
            "• Новинках магазина\n\n"
            "Обычно лифлеты раздают:\n"
            "• На входе в магазин\n"
            "• В почтовые ящики\n"
            "• На стойках информации\n\n"
            "Загрузите четкое фото любого рекламного лифлета.",
            reply_markup=get_photo_upload_keyboard()
        )
    
    @router.message(F.photo, StateFilter(RegistrationStates.WAITING_LEAFLET_PHOTO))
    async def process_photo(message: Message, state: FSMContext):
        """Process leaflet photo"""
        try:
            # Get the largest photo
            photo = message.photo[-1]
            
            # Download and save photo
            photo_path = await save_photo(message.bot, photo.file_id, message.from_user.id)
            
            if not photo_path:
                await message.answer(
                    "❌ Ошибка при сохранении фото!\n\n"
                    "Попробуйте загрузить фото еще раз:",
                    reply_markup=get_photo_upload_keyboard()
                )
                return
            
            await state.update_data(leaflet_photo_path=photo_path)
            await state.set_state(RegistrationStates.CONFIRMATION)
            
            # Show confirmation
            data = await state.get_data()
            
            confirmation_text = (
                "✅ Проверьте введенные данные:\n\n"
                f"👤 Имя: {data['full_name']}\n"
                f"📞 Телефон: {data['phone_number']}\n"
                f"💳 Карта лояльности: {data['loyalty_card']}\n"
                f"📷 Фото лифлета: загружено\n\n"
                "Все данные верны?"
            )
            
            await message.answer(
                confirmation_text,
                reply_markup=get_confirmation_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await message.answer(
                "❌ Ошибка при обработке фото!\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_photo_upload_keyboard()
            )
    
    @router.message(StateFilter(RegistrationStates.WAITING_LEAFLET_PHOTO))
    async def handle_photo_text(message: Message, state: FSMContext):
        """Handle text messages in photo waiting state"""
        if message.text == "⬅️ Назад к карте лояльности":
            await state.set_state(RegistrationStates.WAITING_LOYALTY_CARD)
            await message.answer(
                "💳 Шаг 3 из 4: Введите номер карты лояльности",
                reply_markup=get_loyalty_card_keyboard()
            )
            return
        
        if message.text == "🏠 Главное меню":
            await state.clear()
            await message.answer(
                "Регистрация отменена.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await message.answer(
            "📷 Пожалуйста, загрузите фото лифлета.\n\n"
            "Используйте камеру или выберите готовое изображение из галереи.",
            reply_markup=get_photo_upload_keyboard()
        )
    
    # Confirmation callbacks
    @router.callback_query(F.data == "confirm_registration", StateFilter(RegistrationStates.CONFIRMATION))
    async def confirm_registration(callback: CallbackQuery, state: FSMContext):
        """Confirm and save registration"""
        data = await state.get_data()
        
        try:
            participant_id = db_manager.add_participant(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username or "",
                full_name=data['full_name'],
                phone_number=data['phone_number'],
                loyalty_card=data['loyalty_card'],
                leaflet_photo_path=data['leaflet_photo_path']
            )
            
            await state.clear()
            
            await callback.message.edit_text(
                "🎉 Регистрация успешно завершена!\n\n"
                "✅ Ваша заявка отправлена на рассмотрение.\n"
                "📧 Уведомление о статусе придет в этот чат.\n"
                "🕐 Обычно рассмотрение занимает 1-2 рабочих дня.\n\n"
                "Удачи в розыгрыше! 🍀"
            )
            
            await callback.message.answer(
                "Что хотите сделать дальше?",
                reply_markup=get_main_menu_keyboard()
            )
            
            logger.info(f"User {callback.from_user.id} registered successfully")
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await callback.answer("❌ Ошибка при регистрации. Попробуйте позже.")
    
    # Edit callbacks
    @router.callback_query(F.data == "edit_name", StateFilter(RegistrationStates.CONFIRMATION))
    async def edit_name(callback: CallbackQuery, state: FSMContext):
        """Edit name"""
        await state.set_state(RegistrationStates.WAITING_NAME)
        await callback.message.edit_text(
            "📝 Введите новое имя:",
            reply_markup=None
        )
        await callback.message.answer(
            "Введите ваше полное имя:",
            reply_markup=get_name_input_keyboard()
        )
    
    @router.callback_query(F.data == "cancel_registration", StateFilter(RegistrationStates.CONFIRMATION))
    async def cancel_registration(callback: CallbackQuery, state: FSMContext):
        """Cancel registration"""
        await state.clear()
        await callback.message.edit_text("❌ Регистрация отменена.")
        await callback.message.answer(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    
    return router