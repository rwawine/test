"""
Database manager for DuckDB operations
"""

import duckdb
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages DuckDB database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        
    def connect(self) -> duckdb.DuckDBPyConnection:
        """Create and return database connection"""
        if not self.connection:
            self.connection = duckdb.connect(self.db_path)
        return self.connection
    
    def init_database(self) -> None:
        """Initialize database with all required tables"""
        conn = self.connect()
        
        # Create participants table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id VARCHAR PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR,
                full_name VARCHAR NOT NULL,
                phone_number VARCHAR UNIQUE NOT NULL,
                loyalty_card VARCHAR UNIQUE NOT NULL,
                leaflet_photo_path VARCHAR,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR DEFAULT 'pending',
                admin_notes TEXT
            )
        """)
        
        # Create winners table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                id VARCHAR PRIMARY KEY,
                participant_id VARCHAR NOT NULL,
                draw_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seed_hash VARCHAR NOT NULL,
                draw_number INTEGER DEFAULT 1,
                is_valid BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            )
        """)
        
        # Create admin_logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id VARCHAR PRIMARY KEY,
                admin_id BIGINT NOT NULL,
                action VARCHAR NOT NULL,
                target_participant_id VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (target_participant_id) REFERENCES participants(id)
            )
        """)
        
        # Create support_tickets table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id VARCHAR PRIMARY KEY,
                ticket_number VARCHAR UNIQUE NOT NULL,
                user_id BIGINT NOT NULL,
                username VARCHAR,
                participant_id VARCHAR,
                status VARCHAR DEFAULT 'open',
                priority VARCHAR DEFAULT 'medium',
                subject VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                assigned_admin BIGINT,
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            )
        """)
        
        # Create support_messages table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id VARCHAR PRIMARY KEY,
                ticket_id VARCHAR NOT NULL,
                sender_id BIGINT NOT NULL,
                sender_type VARCHAR NOT NULL,
                message_text TEXT NOT NULL,
                attachment_path VARCHAR,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
            )
        """)
        
        # Create broadcasts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id VARCHAR PRIMARY KEY,
                title VARCHAR NOT NULL,
                message_text TEXT NOT NULL,
                message_type VARCHAR DEFAULT 'text',
                image_path VARCHAR,
                target_audience VARCHAR NOT NULL,
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP,
                status VARCHAR DEFAULT 'draft',
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0
            )
        """)
        
        # Create broadcast_recipients table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_recipients (
                id VARCHAR PRIMARY KEY,
                broadcast_id VARCHAR NOT NULL,
                participant_id VARCHAR,
                telegram_id BIGINT NOT NULL,
                status VARCHAR DEFAULT 'pending',
                sent_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id),
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            )
        """)
        
        logger.info("Database initialized successfully")
    
    # Participant operations
    def add_participant(self, telegram_id: int, username: str, full_name: str, 
                       phone_number: str, loyalty_card: str, 
                       leaflet_photo_path: str = None) -> str:
        """Add new participant and return participant ID"""
        conn = self.connect()
        participant_id = str(uuid.uuid4())
        
        conn.execute("""
            INSERT INTO participants 
            (id, telegram_id, username, full_name, phone_number, loyalty_card, leaflet_photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [participant_id, telegram_id, username, full_name, phone_number, loyalty_card, leaflet_photo_path])
        
        logger.info(f"Added participant {participant_id} (telegram_id: {telegram_id})")
        return participant_id
    
    def get_participant_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get participant by Telegram ID"""
        conn = self.connect()
        result = conn.execute("""
            SELECT * FROM participants WHERE telegram_id = ?
        """, [telegram_id]).fetchone()
        
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None
    
    def get_participant_by_id(self, participant_id: str) -> Optional[Dict]:
        """Get participant by ID"""
        conn = self.connect()
        result = conn.execute("""
            SELECT * FROM participants WHERE id = ?
        """, [participant_id]).fetchone()
        
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None
    
    def update_participant_status(self, participant_id: str, status: str, 
                                admin_id: int, notes: str = None) -> bool:
        """Update participant status"""
        conn = self.connect()
        
        # Update participant
        conn.execute("""
            UPDATE participants 
            SET status = ?, admin_notes = ?
            WHERE id = ?
        """, [status, notes, participant_id])
        
        # Log admin action
        self.log_admin_action(admin_id, "status_change", participant_id, 
                            f"Status changed to {status}")
        
        return True
    
    def check_phone_exists(self, phone_number: str) -> bool:
        """Check if phone number already exists"""
        conn = self.connect()
        result = conn.execute("""
            SELECT COUNT(*) FROM participants WHERE phone_number = ?
        """, [phone_number]).fetchone()
        return result[0] > 0
    
    def check_loyalty_card_exists(self, loyalty_card: str) -> bool:
        """Check if loyalty card already exists"""
        conn = self.connect()
        result = conn.execute("""
            SELECT COUNT(*) FROM participants WHERE loyalty_card = ?
        """, [loyalty_card]).fetchone()
        return result[0] > 0
    
    def get_all_participants(self, status: str = None) -> List[Dict]:
        """Get all participants, optionally filtered by status"""
        conn = self.connect()
        
        if status:
            results = conn.execute("""
                SELECT * FROM participants WHERE status = ? ORDER BY registration_date DESC
            """, [status]).fetchall()
        else:
            results = conn.execute("""
                SELECT * FROM participants ORDER BY registration_date DESC
            """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    # Winner operations
    def add_winner(self, participant_id: str, seed_hash: str, draw_number: int = 1) -> str:
        """Add winner record"""
        conn = self.connect()
        winner_id = str(uuid.uuid4())
        
        conn.execute("""
            INSERT INTO winners (id, participant_id, seed_hash, draw_number)
            VALUES (?, ?, ?, ?)
        """, [winner_id, participant_id, seed_hash, draw_number])
        
        logger.info(f"Added winner {winner_id} (participant: {participant_id})")
        return winner_id
    
    def get_winners(self) -> List[Dict]:
        """Get all winners with participant info"""
        conn = self.connect()
        results = conn.execute("""
            SELECT w.*, p.full_name, p.phone_number, p.telegram_id
            FROM winners w
            JOIN participants p ON w.participant_id = p.id
            WHERE w.is_valid = TRUE
            ORDER BY w.draw_date DESC
        """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    def get_winner_by_id(self, winner_id: str) -> Optional[Dict]:
        """Get winner by ID with participant info"""
        conn = self.connect()
        result = conn.execute("""
            SELECT w.*, p.full_name, p.phone_number, p.telegram_id
            FROM winners w
            JOIN participants p ON w.participant_id = p.id
            WHERE w.id = ?
        """, [winner_id]).fetchone()
        
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None
    
    def invalidate_winner(self, winner_id: str, admin_id: int, reason: str = None) -> bool:
        """Invalidate a winner (for reroll)"""
        try:
            conn = self.connect()
            
            # Invalidate the winner
            conn.execute("""
                UPDATE winners SET is_valid = FALSE WHERE id = ?
            """, [winner_id])
            
            # Log the action
            self.log_admin_action(
                admin_id=admin_id,
                action='invalidate_winner',
                target_participant_id=None,
                details=f'Winner {winner_id} invalidated. Reason: {reason or "No reason provided"}'
            )
            
            logger.info(f"Winner {winner_id} invalidated by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating winner {winner_id}: {e}")
            return False
    
    def delete_winner(self, winner_id: str, admin_id: int) -> bool:
        """Permanently delete a winner record"""
        try:
            conn = self.connect()
            
            # Get winner info before deletion for logging
            winner = self.get_winner_by_id(winner_id)
            if not winner:
                return False
            
            # Delete the winner
            conn.execute("DELETE FROM winners WHERE id = ?", [winner_id])
            
            # Log the action
            self.log_admin_action(
                admin_id=admin_id,
                action='delete_winner',
                target_participant_id=winner.get('participant_id'),
                details=f'Winner record deleted: {winner.get("full_name")} from draw #{winner.get("draw_number")}'
            )
            
            logger.info(f"Winner {winner_id} deleted by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting winner {winner_id}: {e}")
            return False
    
    # Admin logging
    def log_admin_action(self, admin_id: int, action: str, 
                        target_participant_id: str = None, details: str = None) -> str:
        """Log admin action"""
        conn = self.connect()
        log_id = str(uuid.uuid4())
        
        conn.execute("""
            INSERT INTO admin_logs (id, admin_id, action, target_participant_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, [log_id, admin_id, action, target_participant_id, details])
        
        return log_id
    
    # Statistics
    def get_statistics(self) -> Dict[str, Any]:
        """Get general statistics"""
        conn = self.connect()
        
        stats = {}
        
        # Total participants
        result = conn.execute("SELECT COUNT(*) FROM participants").fetchone()
        stats['total_participants'] = result[0]
        
        # Participants by status
        results = conn.execute("""
            SELECT status, COUNT(*) FROM participants GROUP BY status
        """).fetchall()
        stats['by_status'] = {row[0]: row[1] for row in results}
        
        # Total winners
        result = conn.execute("SELECT COUNT(*) FROM winners WHERE is_valid = TRUE").fetchone()
        stats['total_winners'] = result[0]
        
        # Registration trends (last 7 days)
        results = conn.execute("""
            SELECT DATE(registration_date) as date, COUNT(*) as count
            FROM participants 
            WHERE registration_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(registration_date)
            ORDER BY date
        """).fetchall()
        stats['registration_trend'] = {str(row[0]): row[1] for row in results}
        
        return stats
    
    # Support ticket operations
    def create_support_ticket(self, user_id: int, username: str, subject: str, 
                            participant_id: str = None) -> str:
        """Create new support ticket"""
        conn = self.connect()
        ticket_id = str(uuid.uuid4())
        ticket_number = f"T{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        conn.execute("""
            INSERT INTO support_tickets 
            (id, ticket_number, user_id, username, subject, participant_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [ticket_id, ticket_number, user_id, username, subject, participant_id])
        
        logger.info(f"Created support ticket {ticket_number} for user {user_id}")
        return ticket_id
    
    def add_support_message(self, ticket_id: str, sender_id: int, sender_type: str, 
                          message_text: str, attachment_path: str = None) -> str:
        """Add message to support ticket"""
        conn = self.connect()
        message_id = str(uuid.uuid4())
        
        conn.execute("""
            INSERT INTO support_messages 
            (id, ticket_id, sender_id, sender_type, message_text, attachment_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [message_id, ticket_id, sender_id, sender_type, message_text, attachment_path])
        
        # Update ticket timestamp
        conn.execute("""
            UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, [ticket_id])
        
        return message_id
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_support_tickets(self, status: str = None) -> List[Dict]:
        """Get support tickets, optionally filtered by status"""
        conn = self.connect()
        
        if status:
            results = conn.execute("""
                SELECT st.*, p.full_name as participant_name
                FROM support_tickets st
                LEFT JOIN participants p ON st.participant_id = p.id
                WHERE st.status = ?
                ORDER BY st.created_at DESC
            """, [status]).fetchall()
        else:
            results = conn.execute("""
                SELECT st.*, p.full_name as participant_name
                FROM support_tickets st
                LEFT JOIN participants p ON st.participant_id = p.id
                ORDER BY st.created_at DESC
            """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    def get_support_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """Get support ticket by ID"""
        conn = self.connect()
        result = conn.execute("""
            SELECT st.*, p.full_name as participant_name, p.telegram_id
            FROM support_tickets st
            LEFT JOIN participants p ON st.participant_id = p.id
            WHERE st.id = ?
        """, [ticket_id]).fetchone()
        
        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None
    
    def get_support_messages(self, ticket_id: str) -> List[Dict]:
        """Get all messages for a support ticket"""
        conn = self.connect()
        results = conn.execute("""
            SELECT * FROM support_messages 
            WHERE ticket_id = ? 
            ORDER BY sent_at ASC
        """, [ticket_id]).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in results]
    
    def update_support_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update support ticket status"""
        conn = self.connect()
        
        if status == 'closed':
            conn.execute("""
                UPDATE support_tickets 
                SET status = ?, updated_at = CURRENT_TIMESTAMP, closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [status, ticket_id])
        else:
            conn.execute("""
                UPDATE support_tickets 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [status, ticket_id])
        
        return True