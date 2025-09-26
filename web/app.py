"""
Flask web application for admin panel
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os
import logging
from datetime import datetime
from database.db_manager import DatabaseManager
from config import Config
from utils.lottery import LotterySystem
from utils.broadcast import BroadcastSystem
from utils.notifications import NotificationSystem

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    # Set template folder to parent directory's templates folder
    import os
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    
    # Initialize database and systems
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    lottery_system = LotterySystem(db_manager)
    
    # Initialize Bot for broadcast system and notifications
    from aiogram import Bot
    bot = Bot(token=Config.BOT_TOKEN)
    broadcast_system = BroadcastSystem(db_manager, bot)
    notification_system = NotificationSystem(bot)
    
    # Simple admin authentication (in production use proper auth system)
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD_HASH = generate_password_hash("admin123")  # Change this!
    
    @app.context_processor
    def inject_stats():
        """Inject dashboard stats into all templates for navigation"""
        try:
            if session.get('logged_in'):
                stats = db_manager.get_statistics()
                # Ensure by_status exists with default values
                if 'by_status' not in stats:
                    stats['by_status'] = {}
                
                # Ensure all required status keys exist
                for status in ['pending', 'approved', 'rejected']:
                    if status not in stats['by_status']:
                        stats['by_status'][status] = 0
                        
                return {'stats': stats}
        except Exception as e:
            logger.error(f"Error injecting stats: {e}")
        
        # Return safe defaults
        return {
            'stats': {
                'by_status': {'pending': 0, 'approved': 0, 'rejected': 0}, 
                'total_participants': 0,
                'total_winners': 0
            }
        }
    
    def login_required(f):
        """Decorator for login required routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Admin login page"""
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
                session['logged_in'] = True
                flash('Успешный вход в систему', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Неверные учетные данные', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout"""
        session.pop('logged_in', None)
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('login'))
    
    @app.route('/')
    @login_required
    def dashboard():
        """Main dashboard"""
        stats = db_manager.get_statistics()
        recent_participants = db_manager.get_all_participants()[:10]  # Last 10
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_participants=recent_participants)
    
    @app.route('/participants')
    @login_required
    def participants():
        """List all participants"""
        status_filter = request.args.get('status', '')
        search = request.args.get('search', '')
        
        try:
            if status_filter:
                participants_list = db_manager.get_all_participants(status=status_filter)
            else:
                participants_list = db_manager.get_all_participants()
            
            logger.info(f"Found {len(participants_list)} participants.")

            # Simple search by name or phone
            if search:
                participants_list = [
                    p for p in participants_list 
                    if search.lower() in p['full_name'].lower() or 
                       search in p['phone_number']
                ]
        except Exception as e:
            logger.error(f"Error fetching participants: {e}")
            participants_list = []
            flash("Произошла ошибка при загрузке участников.", "error")
        
        return render_template('participants.html', 
                             participants=participants_list,
                             current_status=status_filter,
                             search_query=search)
    
    @app.route('/participant/<participant_id>')
    @login_required
    def participant_detail(participant_id):
        """View participant details"""
        participant = db_manager.get_participant_by_id(participant_id)
        
        if not participant:
            flash('Участник не найден', 'error')
            return redirect(url_for('participants'))
        
        return render_template('participant_detail.html', participant=participant)
    
    @app.route('/participant/<participant_id>/update_status', methods=['POST'])
    @login_required
    def update_participant_status(participant_id):
        """Update participant status"""
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if new_status in ['pending', 'approved', 'rejected']:
            # Get participant info before updating
            participant = db_manager.get_participant_by_id(participant_id)
            if not participant:
                flash('Участник не найден', 'error')
                return redirect(url_for('participants'))
            
            # In a real app, get admin_id from session
            admin_id = 123456789  # Placeholder
            
            success = db_manager.update_participant_status(
                participant_id, new_status, admin_id, notes
            )
            
            if success:
                flash(f'Статус обновлен на: {new_status}', 'success')
                
                # Send notification to participant
                async def send_notification():
                    try:
                        await notification_system.send_status_change_notification(
                            participant['telegram_id'],
                            participant['full_name'],
                            new_status,
                            notes if notes else None
                        )
                    except Exception as e:
                        logger.error(f"Failed to send notification: {e}")
                
                # Run notification in background
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a new thread for the async notification
                        import threading
                        def run_notification():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            new_loop.run_until_complete(send_notification())
                            new_loop.close()
                        
                        notification_thread = threading.Thread(target=run_notification)
                        notification_thread.start()
                    else:
                        loop.run_until_complete(send_notification())
                except RuntimeError:
                    # No event loop, create a new one
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(send_notification())
                    new_loop.close()
                
            else:
                flash('Ошибка при обновлении статуса', 'error')
        else:
            flash('Некорректный статус', 'error')
        
        # If request came from participants list (quick action), redirect there
        if request.referrer and 'participants' in request.referrer:
            return redirect(url_for('participants'))
        else:
            return redirect(url_for('participant_detail', participant_id=participant_id))
    
    @app.route('/participants/mass_action', methods=['POST'])
    @login_required
    def mass_update_status():
        """Mass update participant status"""
        participant_ids = request.form.getlist('participant_ids')
        new_status = request.form.get('status')
        notes = request.form.get('notes', 'Массовое действие')
        
        if not participant_ids:
            flash('Участники не выбраны', 'error')
            return redirect(url_for('participants'))
        
        if new_status not in ['pending', 'approved', 'rejected']:
            flash('Некорректный статус', 'error')
            return redirect(url_for('participants'))
        
        admin_id = 123456789  # Placeholder
        success_count = 0
        participants_to_notify = []
        
        for participant_id in participant_ids:
            # Get participant info before updating
            participant = db_manager.get_participant_by_id(participant_id)
            if participant:
                success = db_manager.update_participant_status(
                    participant_id, new_status, admin_id, notes
                )
                if success:
                    success_count += 1
                    participants_to_notify.append(participant)
        
        # Send notifications to all updated participants
        if participants_to_notify:
            async def send_mass_notifications():
                for participant in participants_to_notify:
                    try:
                        await notification_system.send_status_change_notification(
                            participant['telegram_id'],
                            participant['full_name'],
                            new_status,
                            notes if notes else None
                        )
                    except Exception as e:
                        logger.error(f"Failed to send mass notification to {participant['telegram_id']}: {e}")
            
            # Run notifications in background
            import asyncio
            import threading
            def run_mass_notifications():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(send_mass_notifications())
                new_loop.close()
            
            notification_thread = threading.Thread(target=run_mass_notifications)
            notification_thread.start()
        
        flash(f'Обновлено статусов: {success_count} из {len(participant_ids)}. Уведомления отправляются.', 'success')
        return redirect(url_for('participants'))
    
    @app.route('/photo/<path:filename>')
    @login_required
    def serve_photo(filename):
        """Serve uploaded photos"""
        try:
            # Convert backslashes to forward slashes and remove any path traversal attempts
            filename = filename.replace('\\', '/').replace('..', '')
            file_path = os.path.join(os.getcwd(), filename)
            
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                flash('Файл не найден', 'error')
                return redirect(url_for('participants'))
        except Exception as e:
            flash(f'Ошибка при загрузке файла: {str(e)}', 'error')
            return redirect(url_for('participants'))
    
    @app.route('/export')
    @login_required
    def export_data():
        """Export participants data"""
        import pandas as pd
        from io import BytesIO
        
        participants = db_manager.get_all_participants()
        
        # Convert to DataFrame
        df = pd.DataFrame(participants)
        
        # Create Excel file in memory
        output = BytesIO()
        
        try:
            # Try with xlsxwriter first
            try:
                import xlsxwriter
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Participants', index=False)
                    
                    # Get workbook and worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Participants']
                    
                    # Add formatting
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Apply header format
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Adjust column widths
                    for i, column in enumerate(df.columns):
                        worksheet.set_column(i, i, 15)
                        
                logger.info("Excel export successful using xlsxwriter")
                
            except ImportError:
                # Fallback to openpyxl
                try:
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Participants', index=False)
                    logger.info("Excel export successful using openpyxl")
                except ImportError:
                    # Final fallback - basic CSV export as Excel
                    df.to_csv(output, index=False, encoding='utf-8-sig')
                    logger.info("Export successful using CSV format")
                    
        except Exception as e:
            logger.error(f"Export error: {e}")
            flash(f'Ошибка при экспорте: {str(e)}', 'error')
            return redirect(url_for('participants'))
        
        output.seek(0)
        
        filename = f"participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        """Get dashboard statistics"""
        try:
            stats = db_manager.get_statistics()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/lottery')
    @login_required
    def lottery():
        """Lottery management page"""
        lottery_stats = lottery_system.get_lottery_statistics()
        dashboard_stats = db_manager.get_statistics()  # For base template
        winners = db_manager.get_winners()
        eligible = lottery_system.get_eligible_participants()
        
        return render_template('lottery.html', 
                             lottery_stats=lottery_stats,
                             stats=dashboard_stats,  # For base template navigation
                             winners=winners,
                             eligible_count=len(eligible))
    
    @app.route('/lottery/conduct', methods=['POST'])
    @login_required
    def conduct_lottery():
        """Conduct lottery draw"""
        try:
            num_winners = int(request.form.get('num_winners', 1))
            
            result = lottery_system.conduct_lottery(num_winners)
            
            flash(f'Lottery completed! {len(result["winners"])} winners selected.', 'success')
            
            # TODO: Send notifications to winners
            
        except Exception as e:
            flash(f'Error conducting lottery: {str(e)}', 'error')
        
        return redirect(url_for('lottery_page'))
    
    @app.route('/lottery/reroll_winner/<winner_id>', methods=['POST'])
    @login_required
    def reroll_winner(winner_id):
        """Reroll a specific winner"""
        try:
            reason = request.form.get('reason', '').strip()
            admin_id = 123456789  # TODO: Get from session
            
            result = lottery_system.reroll_winner(winner_id, admin_id, reason)
            
            flash(f'Перерозыгрыш выполнен! Новый победитель: {result["new_winner"]["participant"]["full_name"]}', 'success')
            
            # TODO: Send notifications to both old and new winners
            
        except Exception as e:
            flash(f'Ошибка при перерозыгрыше: {str(e)}', 'error')
        
        return redirect(url_for('lottery_page'))
    
    @app.route('/lottery/delete_winner/<winner_id>', methods=['POST'])
    @login_required
    def delete_winner(winner_id):
        """Delete a winner completely"""
        try:
            admin_id = 123456789  # TODO: Get from session
            
            success = lottery_system.delete_winner_completely(winner_id, admin_id)
            
            if success:
                flash('Победитель удален! Участник снова может участвовать в розыгрышах.', 'success')
            else:
                flash('Ошибка при удалении победителя', 'error')
                
        except Exception as e:
            flash(f'Ошибка при удалении победителя: {str(e)}', 'error')
        
        return redirect(url_for('lottery_page'))
    
    @app.route('/lottery/winner/<winner_id>')
    @login_required
    def winner_detail(winner_id):
        """View winner details"""
        winner = db_manager.get_winner_by_id(winner_id)
        if not winner:
            flash('Информация о победителе не найдена', 'error')
            return redirect(url_for('lottery_page'))
        
        # Get participant details
        participant = db_manager.get_participant_by_id(winner['participant_id'])
        
        return render_template('winner_detail.html', 
                             winner=winner,
                             participant=participant)
    
    @app.route('/api/lottery_stats')
    @login_required
    def api_lottery_stats():
        """API endpoint for lottery statistics"""
        try:
            lottery_system = LotterySystem(db_manager)
            eligible_participants = lottery_system.get_eligible_participants()
            stats = lottery_system.get_lottery_statistics()
            
            return jsonify({
                'eligible_count': len(eligible_participants),
                'total_draws': stats['total_draws'],
                'total_winners': stats['total_winners'],
                'total_participants': stats['total_participants'],
                'win_rate': stats['win_rate']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/broadcasts')
    @login_required
    def broadcasts():
        """Broadcast management page"""
        broadcasts = broadcast_system.get_broadcast_list()
        templates = broadcast_system.get_broadcast_templates()
        
        return render_template('broadcasts.html', 
                             broadcasts=broadcasts,
                             templates=templates)
    
    @app.route('/broadcasts/create', methods=['POST'])
    @login_required
    def create_broadcast():
        """Create new broadcast"""
        try:
            title = request.form.get('title')
            message_text = request.form.get('message_text')
            target_audience = request.form.get('target_audience')
            admin_id = 123456789  # TODO: Get from session
            
            broadcast_id = broadcast_system.create_broadcast(
                title=title,
                message_text=message_text,
                target_audience=target_audience,
                created_by=admin_id
            )
            
            flash(f'Broadcast created successfully! ID: {broadcast_id}', 'success')
            
        except Exception as e:
            flash(f'Error creating broadcast: {str(e)}', 'error')
        
        return redirect(url_for('broadcasts'))
    
    @app.route('/broadcasts/<broadcast_id>/send', methods=['POST'])
    @login_required
    def send_broadcast(broadcast_id):
        """Send a broadcast"""
        try:
            import asyncio
            
            # Run the async broadcast function
            result = asyncio.run(broadcast_system.send_broadcast(broadcast_id))
            
            flash(f'Broadcast sent! {result["sent_count"]} messages delivered, {result["failed_count"]} failed.', 'success')
            
        except Exception as e:
            flash(f'Error sending broadcast: {str(e)}', 'error')
        
        return redirect(url_for('broadcasts'))
    
    @app.route('/api/broadcast/<broadcast_id>')
    @login_required
    def api_get_broadcast(broadcast_id):
        """Get broadcast details via API"""
        try:
            broadcast = broadcast_system.get_broadcast_by_id(broadcast_id)
            if broadcast:
                return jsonify(broadcast)
            else:
                return jsonify({'error': 'Broadcast not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/broadcasts/<broadcast_id>/edit', methods=['POST'])
    @login_required
    def edit_broadcast(broadcast_id):
        """Edit broadcast"""
        try:
            title = request.form.get('title')
            message_text = request.form.get('message_text')
            target_audience = request.form.get('target_audience')
            
            success = broadcast_system.update_broadcast(
                broadcast_id=broadcast_id,
                title=title,
                message_text=message_text,
                target_audience=target_audience
            )
            
            if success:
                flash('Рассылка успешно обновлена!', 'success')
            else:
                flash('Ошибка при обновлении рассылки', 'error')
                
        except Exception as e:
            flash(f'Ошибка при обновлении рассылки: {str(e)}', 'error')
        
        return redirect(url_for('broadcasts'))
    
    @app.route('/broadcasts/<broadcast_id>/delete', methods=['DELETE', 'POST'])
    @login_required
    def delete_broadcast(broadcast_id):
        """Delete broadcast"""
        try:
            success = broadcast_system.delete_broadcast(broadcast_id)
            
            if success:
                if request.method == 'DELETE':
                    return jsonify({'success': True, 'message': 'Рассылка удалена'})
                else:
                    flash('Рассылка успешно удалена!', 'success')
            else:
                if request.method == 'DELETE':
                    return jsonify({'success': False, 'message': 'Ошибка при удалении'}), 500
                else:
                    flash('Ошибка при удалении рассылки', 'error')
                    
        except Exception as e:
            if request.method == 'DELETE':
                return jsonify({'success': False, 'message': str(e)}), 500
            else:
                flash(f'Ошибка при удалении рассылки: {str(e)}', 'error')
        
        if request.method == 'DELETE':
            return jsonify({'success': True})
        else:
            return redirect(url_for('broadcasts'))
    
    @app.route('/api/broadcast_recipients/<broadcast_id>')
    @login_required
    def api_broadcast_recipients(broadcast_id):
        """Get broadcast recipients count"""
        try:
            recipients = broadcast_system.get_broadcast_recipients(broadcast_id)
            return jsonify({
                'total_count': len(recipients),
                'recipients': recipients[:10]  # First 10 for preview
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/broadcast_recipients')
    @login_required  
    def api_broadcast_recipients_count():
        """Get recipient count for target audience"""
        try:
            audience = request.args.get('audience', 'all')
            recipients = broadcast_system._get_target_recipients(audience)
            return jsonify({
                'count': len(recipients),
                'audience': audience
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/support_tickets')
    @login_required
    def support_tickets():
        """Support tickets management page"""
        status_filter = request.args.get('status', '')
        tickets = db_manager.get_support_tickets(status=status_filter if status_filter else None)
        
        return render_template('support_tickets.html', 
                             tickets=tickets,
                             current_status=status_filter)
    
    @app.route('/support_tickets/<ticket_id>')
    @login_required
    def support_ticket_detail(ticket_id):
        """Support ticket detail page"""
        ticket = db_manager.get_support_ticket_by_id(ticket_id)
        if not ticket:
            flash('Тикет не найден', 'error')
            return redirect(url_for('support_tickets'))
        
        messages = db_manager.get_support_messages(ticket_id)
        return render_template('support_ticket_detail.html', 
                             ticket=ticket,
                             messages=messages)
    
    @app.route('/support_tickets/<ticket_id>/respond', methods=['POST'])
    @login_required
    def respond_to_ticket(ticket_id):
        """Respond to support ticket"""
        try:
            response_text = request.form.get('response')
            if not response_text:
                flash('Ответ не может быть пустым', 'error')
                return redirect(url_for('support_ticket_detail', ticket_id=ticket_id))
            
            # Add admin response
            admin_id = 123456789  # TODO: Get from session
            db_manager.add_support_message(
                ticket_id=ticket_id,
                sender_id=admin_id,
                sender_type='admin',
                message_text=response_text
            )
            
            # Send notification to user
            ticket = db_manager.get_support_ticket_by_id(ticket_id)
            if ticket:
                async def send_response_notification():
                    try:
                        await notification_system.send_support_response_notification(
                            ticket['user_id'],
                            ticket['ticket_number'],
                            response_text
                        )
                    except Exception as e:
                        logger.error(f"Failed to send support response notification: {e}")
                
                # Run notification in background
                import asyncio
                import threading
                def run_notification():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(send_response_notification())
                    new_loop.close()
                
                notification_thread = threading.Thread(target=run_notification)
                notification_thread.start()
            
            flash('Ответ отправлен!', 'success')
            
        except Exception as e:
            flash(f'Ошибка при отправке ответа: {str(e)}', 'error')
        
        return redirect(url_for('support_ticket_detail', ticket_id=ticket_id))
    
    @app.route('/support_tickets/<ticket_id>/status', methods=['POST'])
    @login_required
    def update_ticket_status(ticket_id):
        """Update support ticket status"""
        try:
            new_status = request.form.get('status')
            if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
                flash('Некорректный статус', 'error')
                return redirect(url_for('support_ticket_detail', ticket_id=ticket_id))
            
            # Update ticket status in database
            conn = db_manager.connect()
            conn.execute("""
                UPDATE support_tickets SET status = ? WHERE id = ?
            """, [new_status, ticket_id])
            
            status_names = {
                'open': 'Открыт',
                'in_progress': 'В работе',
                'resolved': 'Решен',
                'closed': 'Закрыт'
            }
            
            flash(f'Статус тикета изменен на: {status_names[new_status]}', 'success')
            
        except Exception as e:
            flash(f'Ошибка при обновлении статуса: {str(e)}', 'error')
        
        return redirect(url_for('support_ticket_detail', ticket_id=ticket_id))
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            stats = db_manager.get_statistics()
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'participants': stats.get('total_participants', 0)
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon requests"""
        from flask import abort
        abort(404)
    
    return app