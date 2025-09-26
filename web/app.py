"""
Flask web application for admin panel
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os
from datetime import datetime
from database import DatabaseManager
from config import Config
from utils.lottery import LotterySystem
from utils.broadcast import BroadcastSystem

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    
    # Initialize database and systems
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    lottery_system = LotterySystem(db_manager)
    broadcast_system = BroadcastSystem(db_manager)
    
    # Simple admin authentication (in production use proper auth system)
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD_HASH = generate_password_hash("admin123")  # Change this!
    
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
        
        if status_filter:
            participants_list = db_manager.get_all_participants(status=status_filter)
        else:
            participants_list = db_manager.get_all_participants()
        
        # Simple search by name or phone
        if search:
            participants_list = [
                p for p in participants_list 
                if search.lower() in p['full_name'].lower() or 
                   search in p['phone_number']
            ]
        
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
            # In a real app, get admin_id from session
            admin_id = 123456789  # Placeholder
            
            success = db_manager.update_participant_status(
                participant_id, new_status, admin_id, notes
            )
            
            if success:
                flash(f'Статус обновлен на: {new_status}', 'success')
            else:
                flash('Ошибка при обновлении статуса', 'error')
        else:
            flash('Некорректный статус', 'error')
        
        return redirect(url_for('participant_detail', participant_id=participant_id))
    
    @app.route('/photo/<path:filename>')
    @login_required
    def serve_photo(filename):
        """Serve uploaded photos"""
        try:
            return send_file(filename)
        except FileNotFoundError:
            flash('Файл не найден', 'error')
            return redirect(url_for('participants'))
    
    @app.route('/export')
    @login_required
    def export_data():
        """Export participants data"""
        import pandas as pd
        from io import BytesIO
        import xlsxwriter
        
        participants = db_manager.get_all_participants()
        
        # Convert to DataFrame
        df = pd.DataFrame(participants)
        
        # Create Excel file in memory
        output = BytesIO()
        
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
        """API endpoint for statistics"""
        stats = db_manager.get_statistics()
        return jsonify(stats)
    
    @app.route('/lottery')
    @login_required
    def lottery_page():
        """Lottery management page"""
        stats = lottery_system.get_lottery_statistics()
        winners = db_manager.get_winners()
        eligible = lottery_system.get_eligible_participants()
        
        return render_template('lottery.html', 
                             stats=stats, 
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
    
    return app