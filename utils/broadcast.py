"""
Broadcast system for mass messaging via Telegram
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from database import DatabaseManager

logger = logging.getLogger(__name__)

class BroadcastSystem:
    """System for managing and sending mass messages"""
    
    def __init__(self, db_manager: DatabaseManager, bot: Bot = None):
        self.db_manager = db_manager
        self.bot = bot
    
    def create_broadcast(self, title: str, message_text: str, target_audience: str,
                        created_by: int, message_type: str = 'text',
                        image_path: str = None, scheduled_at: datetime = None) -> str:
        """
        Create new broadcast campaign
        
        Args:
            title: Broadcast title/name
            message_text: Message content
            target_audience: Target audience ('all', 'approved', 'pending', 'winners')
            created_by: Admin Telegram ID
            message_type: 'text' or 'photo'
            image_path: Path to image file (if message_type is 'photo')
            scheduled_at: When to send (None for immediate)
            
        Returns:
            Broadcast ID
        """
        conn = self.db_manager.connect()
        
        import uuid
        broadcast_id = str(uuid.uuid4())
        
        # Get target recipients
        recipients = self._get_target_recipients(target_audience)
        total_recipients = len(recipients)
        
        # Insert broadcast record
        conn.execute("""
            INSERT INTO broadcasts 
            (id, title, message_text, message_type, image_path, target_audience,
             created_by, scheduled_at, total_recipients)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [broadcast_id, title, message_text, message_type, image_path,
              target_audience, created_by, scheduled_at, total_recipients])
        
        # Insert recipient records
        for participant in recipients:
            recipient_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO broadcast_recipients
                (id, broadcast_id, participant_id, telegram_id)
                VALUES (?, ?, ?, ?)
            """, [recipient_id, broadcast_id, participant.get('id'), participant['telegram_id']])
        
        logger.info(f"Created broadcast {broadcast_id} for {total_recipients} recipients")
        return broadcast_id
    
    def _get_target_recipients(self, target_audience: str) -> List[Dict]:
        """Get list of recipients based on target audience"""
        if target_audience == 'all':
            return self.db_manager.get_all_participants()
        elif target_audience == 'approved':
            return self.db_manager.get_all_participants(status='approved')
        elif target_audience == 'pending':
            return self.db_manager.get_all_participants(status='pending')
        elif target_audience == 'rejected':
            return self.db_manager.get_all_participants(status='rejected')
        elif target_audience == 'winners':
            winners = self.db_manager.get_winners()
            winner_participant_ids = [w['participant_id'] for w in winners]
            participants = self.db_manager.get_all_participants()
            return [p for p in participants if p['id'] in winner_participant_ids]
        else:
            raise ValueError(f"Unknown target audience: {target_audience}")
    
    async def send_broadcast(self, broadcast_id: str, bot: Bot = None) -> Dict:
        """
        Send broadcast messages
        
        Args:
            broadcast_id: ID of broadcast to send
            bot: Telegram bot instance
            
        Returns:
            Results dictionary
        """
        if bot:
            self.bot = bot
        
        if not self.bot:
            raise ValueError("Bot instance is required for sending messages")
        
        conn = self.db_manager.connect()
        
        # Get broadcast info
        broadcast_info = conn.execute("""
            SELECT * FROM broadcasts WHERE id = ?
        """, [broadcast_id]).fetchone()
        
        if not broadcast_info:
            raise ValueError(f"Broadcast {broadcast_id} not found")
        
        # Convert to dict
        columns = [desc[0] for desc in conn.description]
        broadcast = dict(zip(columns, broadcast_info))
        
        # Update status to 'sending'
        conn.execute("""
            UPDATE broadcasts SET status = 'sending' WHERE id = ?
        """, [broadcast_id])
        
        # Get recipients
        recipients = conn.execute("""
            SELECT * FROM broadcast_recipients 
            WHERE broadcast_id = ? AND status = 'pending'
        """, [broadcast_id]).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        recipients = [dict(zip(columns, row)) for row in recipients]
        
        # Send messages
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                success = await self._send_single_message(
                    recipient['telegram_id'],
                    broadcast['message_text'],
                    broadcast['message_type'],
                    broadcast['image_path']
                )
                
                if success:
                    # Update recipient status
                    conn.execute("""
                        UPDATE broadcast_recipients 
                        SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, [recipient['id']])
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting - wait between messages
                await asyncio.sleep(0.1)  # 100ms delay
                
            except Exception as e:
                logger.error(f"Failed to send to {recipient['telegram_id']}: {e}")
                
                # Update recipient with error
                conn.execute("""
                    UPDATE broadcast_recipients 
                    SET status = 'failed', error_message = ?
                    WHERE id = ?
                """, [str(e), recipient['id']])
                failed_count += 1
        
        # Update broadcast statistics
        conn.execute("""
            UPDATE broadcasts 
            SET status = 'completed', sent_count = ?, failed_count = ?
            WHERE id = ?
        """, [sent_count, failed_count, broadcast_id])
        
        result = {
            'broadcast_id': broadcast_id,
            'total_recipients': len(recipients),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'success_rate': (sent_count / len(recipients) * 100) if recipients else 0
        }
        
        logger.info(f"Broadcast {broadcast_id} completed: {sent_count} sent, {failed_count} failed")
        return result
    
    async def _send_single_message(self, telegram_id: int, message_text: str,
                                 message_type: str, image_path: str = None) -> bool:
        """Send single message to user"""
        try:
            if message_type == 'photo' and image_path:
                from aiogram.types import FSInputFile
                photo = FSInputFile(image_path)
                await self.bot.send_photo(
                    chat_id=telegram_id,
                    photo=photo,
                    caption=message_text
                )
            else:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message_text
                )
            
            return True
            
        except TelegramForbiddenError:
            # User blocked the bot
            logger.warning(f"User {telegram_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            # Invalid user ID or other error
            logger.warning(f"Bad request for user {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to {telegram_id}: {e}")
            return False
    
    def get_broadcast_list(self) -> List[Dict]:
        """Get list of all broadcasts"""
        conn = self.db_manager.connect()
        
        results = conn.execute("""
            SELECT * FROM broadcasts ORDER BY created_at DESC
        """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    def get_broadcast_details(self, broadcast_id: str) -> Optional[Dict]:
        """Get detailed broadcast information"""
        conn = self.db_manager.connect()
        
        # Get broadcast info
        broadcast_info = conn.execute("""
            SELECT * FROM broadcasts WHERE id = ?
        """, [broadcast_id]).fetchone()
        
        if not broadcast_info:
            return None
        
        columns = [desc[0] for desc in conn.description]
        broadcast = dict(zip(columns, broadcast_info))
        
        # Get recipient statistics
        recipient_stats = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM broadcast_recipients 
            WHERE broadcast_id = ?
            GROUP BY status
        """, [broadcast_id]).fetchall()
        
        broadcast['recipient_stats'] = {row[0]: row[1] for row in recipient_stats}
        
        return broadcast
    
    def get_broadcast_recipients(self, broadcast_id: str, status: str = None) -> List[Dict]:
        """Get recipients of a broadcast with optional status filter"""
        conn = self.db_manager.connect()
        
        if status:
            results = conn.execute("""
                SELECT br.*, p.full_name, p.username
                FROM broadcast_recipients br
                LEFT JOIN participants p ON br.participant_id = p.id
                WHERE br.broadcast_id = ? AND br.status = ?
                ORDER BY br.sent_at DESC
            """, [broadcast_id, status]).fetchall()
        else:
            results = conn.execute("""
                SELECT br.*, p.full_name, p.username
                FROM broadcast_recipients br
                LEFT JOIN participants p ON br.participant_id = p.id
                WHERE br.broadcast_id = ?
                ORDER BY br.sent_at DESC
            """, [broadcast_id]).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    def cancel_broadcast(self, broadcast_id: str) -> bool:
        """Cancel pending broadcast"""
        conn = self.db_manager.connect()
        
        # Check if broadcast can be cancelled
        broadcast = conn.execute("""
            SELECT status FROM broadcasts WHERE id = ?
        """, [broadcast_id]).fetchone()
        
        if not broadcast or broadcast[0] in ['completed', 'cancelled']:
            return False
        
        # Cancel broadcast
        conn.execute("""
            UPDATE broadcasts SET status = 'cancelled' WHERE id = ?
        """, [broadcast_id])
        
        # Cancel pending recipients
        conn.execute("""
            UPDATE broadcast_recipients 
            SET status = 'cancelled' 
            WHERE broadcast_id = ? AND status = 'pending'
        """, [broadcast_id])
        
        logger.info(f"Broadcast {broadcast_id} cancelled")
        return True
    
    def update_broadcast(self, broadcast_id: str, title: str = None, 
                        message_text: str = None, target_audience: str = None) -> bool:
        """Update broadcast details (only for draft broadcasts)"""
        conn = self.db_manager.connect()
        
        # Check if broadcast can be updated
        broadcast = conn.execute("""
            SELECT status FROM broadcasts WHERE id = ?
        """, [broadcast_id]).fetchone()
        
        if not broadcast or broadcast[0] != 'draft':
            return False
        
        # Build update query dynamically
        updates = []
        params = []
        
        if title is not None:
            updates.append('title = ?')
            params.append(title)
        
        if message_text is not None:
            updates.append('message_text = ?')
            params.append(message_text)
        
        if target_audience is not None:
            updates.append('target_audience = ?')
            params.append(target_audience)
            
            # Update recipients if target audience changed
            recipients = self._get_target_recipients(target_audience)
            total_recipients = len(recipients)
            
            # Delete old recipients
            conn.execute("""
                DELETE FROM broadcast_recipients WHERE broadcast_id = ?
            """, [broadcast_id])
            
            # Insert new recipients
            for participant in recipients:
                import uuid
                recipient_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO broadcast_recipients
                    (id, broadcast_id, participant_id, telegram_id)
                    VALUES (?, ?, ?, ?)
                """, [recipient_id, broadcast_id, participant.get('id'), participant['telegram_id']])
            
            updates.append('total_recipients = ?')
            params.append(total_recipients)
        
        if not updates:
            return True  # Nothing to update
        
        # Execute update
        params.append(broadcast_id)
        query = f"UPDATE broadcasts SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        
        logger.info(f"Broadcast {broadcast_id} updated")
        return True
    
    def delete_broadcast(self, broadcast_id: str) -> bool:
        """Delete broadcast (only draft or completed broadcasts)"""
        conn = self.db_manager.connect()
        
        # Check if broadcast can be deleted
        broadcast = conn.execute("""
            SELECT status FROM broadcasts WHERE id = ?
        """, [broadcast_id]).fetchone()
        
        if not broadcast or broadcast[0] == 'sending':
            return False  # Can't delete broadcasts being sent
        
        # Delete recipients first (foreign key constraint)
        conn.execute("""
            DELETE FROM broadcast_recipients WHERE broadcast_id = ?
        """, [broadcast_id])
        
        # Delete broadcast
        conn.execute("""
            DELETE FROM broadcasts WHERE id = ?
        """, [broadcast_id])
        
        logger.info(f"Broadcast {broadcast_id} deleted")
        return True
    
    def get_broadcast_templates(self) -> Dict[str, str]:
        """Get common broadcast message templates"""
        templates = {
            'registration_approved': """
🎉 Поздравляем! Ваша заявка одобрена!

Вы успешно зарегистрированы в розыгрыше призов.
Следите за объявлением результатов в этом чате.

Удачи! 🍀
            """.strip(),
            
            'registration_rejected': """
❌ К сожалению, ваша заявка была отклонена.

Возможные причины:
• Некорректные данные
• Неподходящее фото лифлета
• Нарушение правил участия

Обратитесь в техподдержку для уточнения деталей.
            """.strip(),
            
            'lottery_announcement': """
🎲 Внимание! Розыгрыш призов состоится завтра!

📅 Дата: {date}
🕐 Время: {time}
📺 Трансляция: {channel}

Всем участникам желаем удачи! 🍀
            """.strip(),
            
            'winner_notification': """
🎉 ПОЗДРАВЛЯЕМ! ВЫ ВЫИГРАЛИ!

Вы стали одним из победителей нашего розыгрыша!

📞 Для получения приза свяжитесь с нами:
{contact_info}

Поздравляем с победой! 🏆
            """.strip(),
            
            'technical_notification': """
🔧 Техническое уведомление

{message}

Спасибо за понимание!
            """.strip()
        }
        
        return templates