from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, socketio
from app.models import User, Message, VerificationCode
from flask_socketio import emit
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('main.admin'))
        else:
            return redirect(url_for('main.chat'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required', 'login')
            return render_template('login.html')
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('main.admin'))
            else:
                return redirect(url_for('main.chat'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'login')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        verification_code = request.form.get('verification_code')

        code = VerificationCode.query.filter_by(code=verification_code).first()
        if not code or not code.is_valid():
            flash('Invalid or expired verification code', 'danger')
        else:
            # 检查用户名的唯一性
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'danger')
            else:
                if not username or not password:
                    flash('Username and password are required', 'danger')
                else:
                    user = User(username=username)
                    user.password = password  # 使用setter方法设置密码
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    return redirect(url_for('main.chat'))
    return render_template('register.html')

@main.route('/chat')
@login_required
def chat():
    messages = Message.query.order_by(Message.date_posted).all()
    return render_template('chat.html', messages=messages)

@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('main.chat'))
    if request.method == 'POST':
        code = request.form.get('code')
        start_at = request.form.get('start_at')
        expires_at = request.form.get('expires_at')
        new_code = VerificationCode(
            code=code,
            start_at=datetime.strptime(start_at, '%Y-%m-%dT%H:%M') if start_at else None,
            expires_at=datetime.strptime(expires_at, '%Y-%m-%dT%H:%M') if expires_at else None
        )
        db.session.add(new_code)
        db.session.commit()
        flash('Verification code created successfully', 'success')
        return redirect(url_for('main.admin'))
    codes = VerificationCode.query.all()
    users = User.query.all()
    return render_template('admin.html', codes=codes, users=users)

@main.route('/delete_code/<int:code_id>', methods=['POST'])
@login_required
def delete_code(code_id):
    if not current_user.is_admin:
        return redirect(url_for('main.chat'))
    code = VerificationCode.query.get(code_id)
    if code:
        db.session.delete(code)
        db.session.commit()
        flash('Verification code deleted successfully', 'success')
    return redirect(url_for('main.admin'))

@main.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.chat'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    return redirect(url_for('main.admin'))

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@socketio.on('message')
def handle_message(data):
    message = Message(user_id=current_user.id, content=data['msg'])
    db.session.add(message)
    db.session.commit()
    emit('message', {'user': current_user.username, 'msg': data['msg']}, broadcast=True)