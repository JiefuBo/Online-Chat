from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, socketio
from app.models import User, Message
from flask_socketio import emit

main = Blueprint('main', __name__)

VERIFICATION_CODE = "123456"  # 这个可以从配置文件或数据库读取

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for('main.chat'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')



@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        verification_code = request.form.get('verification_code')

        if verification_code != VERIFICATION_CODE:
            flash('Invalid verification code', 'danger')
        else:
            # 检查用户名的唯一性
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'danger')
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

@main.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('main.chat'))
    return render_template('admin.html')

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
    emit('message', {'user': 'Anonymous', 'msg': data['msg']}, broadcast=True)
