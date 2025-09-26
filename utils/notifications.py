"""
Notification system for participant status updates
"""

import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from typing import Optional

logger = logging.getLogger(__name__)

class NotificationSystem:
    """System for sending notifications to participants"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_approval_notification(self, telegram_id: int, participant_name: str, admin_notes: str = None) -> bool:
        """
        Send approval notification to participant
        
        Args:
            telegram_id: Participant's Telegram ID
            participant_name: Participant's full name
            admin_notes: Optional admin notes
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            message = (
                f"🎉 Поздравляем, {participant_name}!\n\n"
                "✅ Ваша заявка одобрена!\n\n"
                "Вы успешно зарегистрированы в розыгрыше призов.\n"
                "Следите за объявлением результатов в этом чате.\n\n"
            )
            
            if admin_notes:
                message += f"📝 Комментарий администратора:\n{admin_notes}\n\n"
            
            message += "Удачи! 🍀"
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message
            )
            
            logger.info(f"Approval notification sent to {telegram_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {telegram_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"Bad request for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send approval notification to {telegram_id}: {e}")
            return False
    
    async def send_rejection_notification(self, telegram_id: int, participant_name: str, reason: str = None) -> bool:
        """
        Send rejection notification to participant
        
        Args:
            telegram_id: Participant's Telegram ID
            participant_name: Participant's full name
            reason: Reason for rejection
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            message = (
                f"❌ {participant_name}, к сожалению, ваша заявка была отклонена.\n\n"
            )
            
            if reason:
                message += f"📝 Комментарий администратора:\n{reason}\n\n"
            else:
                message += (
                    "Возможные причины:\n"
                    "• Некорректные данные\n"
                    "• Неподходящее фото лифлета\n"
                    "• Нарушение правил участия\n\n"
                )
            
            message += (
                "🆘 Если у вас есть вопросы, обратитесь в техподдержку через кнопку '💬 Техподдержка' в главном меню.\n\n"
                "Вы можете подать новую заявку, исправив указанные замечания."
            )
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message
            )
            
            logger.info(f"Rejection notification sent to {telegram_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {telegram_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"Bad request for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send rejection notification to {telegram_id}: {e}")
            return False
    
    async def send_status_change_notification(self, telegram_id: int, participant_name: str, 
                                            new_status: str, admin_notes: str = None) -> bool:
        """
        Send general status change notification
        
        Args:
            telegram_id: Participant's Telegram ID
            participant_name: Participant's full name
            new_status: New status (approved/rejected/pending)
            admin_notes: Optional admin notes
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if new_status == 'approved':
            return await self.send_approval_notification(telegram_id, participant_name, admin_notes)
        elif new_status == 'rejected':
            return await self.send_rejection_notification(telegram_id, participant_name, admin_notes)
        else:
            # For pending or other statuses, send a generic notification
            try:
                status_text = {
                    'pending': '⏳ На рассмотрении'
                }.get(new_status, new_status)
                
                message = (
                    f"📋 {participant_name}, статус вашей заявки изменен.\n\n"
                    f"Новый статус: {status_text}\n\n"
                )
                
                if admin_notes:
                    message += f"📝 Комментарий администратора:\n{admin_notes}\n\n"
                
                message += "Проверить актуальный статус можно через кнопку '📋 Мой статус' в главном меню."
                
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message
                )
                
                logger.info(f"Status change notification sent to {telegram_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send status change notification to {telegram_id}: {e}")
                return False
    
    async def send_support_response_notification(self, telegram_id: int, participant_name: str, 
                                               ticket_number: str, response_text: str) -> bool:
        """
        Send support response notification to participant
        
        Args:
            telegram_id: Participant's Telegram ID
            participant_name: Participant's full name
            ticket_number: Support ticket number
            response_text: Admin's response text
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            message = (
                f"💬 {participant_name}, вы получили ответ на обращение!\n\n"
                f"🎫 Обращение №{ticket_number}\n\n"
                f"📝 Ответ администратора:\n{response_text}\n\n"
                f"🔄 Если у вас остались вопросы, обратитесь в техподдержку через кнопку '💬 Техподдержка'."
            )
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message
            )
            
            logger.info(f"Support response notification sent to {telegram_id} for ticket {ticket_number}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {telegram_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"Bad request for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send support response notification to {telegram_id}: {e}")
            return False