from flask import render_template, url_for, flash, redirect, request, jsonify, abort
from flask import current_app as app
from app import db, bcrypt, socketio
from app.forms import RegistrationForm, LoginForm, PersonalityForm, EditBirthdayForm, EditGenderPronounsForm, ChatForm
from app.models import User, ChatMessage
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from flask_socketio import emit
from app.ollama import generate_ai_response
import json

@app.route("/")
@app.route("/home", methods=['GET'])
def home():
    return render_template('home.html', title='Home')

@app.route("/chat", methods=['GET', 'POST'])
@login_required
def chat():
    form = ChatForm()
    messages = ChatMessage.query.order_by(ChatMessage.timestamp.asc())
    return render_template('chat.html', title='Chat', form=form, messages=messages)

@socketio.on('message')
@login_required
def handleMessage(msg):
    msg = msg.strip()
    if msg:
        existing_messages = ChatMessage.query.filter_by(message=msg, user_id=current_user.id).all()
        if not existing_messages:
            try:
                chat = ChatMessage(message=msg, username=current_user.username, user_id=current_user.id)
                db.session.add(chat)
                db.session.commit()

                emit('message', {
                    'username': current_user.username,
                    'message': msg,
                    'timestamp': chat.timestamp.strftime("%H:%M")
                }, broadcast=True)
            except Exception as e:
                db.session.rollback()
                print(f"Error handling message: {e}")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, birth_date=form.birth_date.data,
                    password=hashed_password, is_profile_complete=bool(form.birth_date.data))
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.user_id.data) | (User.email == form.user_id.data)).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            if not user.is_profile_complete:
                flash('Please complete your profile.', 'warning')
                return redirect(url_for('edit_profile'))
            next_page = request.args.get('next')
            return redirect(next_page) if next_page and next_page.startswith('/') else redirect(url_for('home'))
        flash('Login Unsuccessful. Please check your username/email and password', 'danger')
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/get_ai_response', methods=['POST'])
@login_required
def get_ai_response():
    data = request.get_json()

    if not data or 'message' not in data:
        abort(400, description="Missing 'message' parameter in JSON data.")
    
    user_message = data['message']
    previous_messages = ChatMessage.query.order_by(ChatMessage.timestamp.asc()).all()
    
    chat_history = [{'role': 'user' if msg.is_user else 'assistant', 'content': msg.message} for msg in previous_messages]
    chat_history.append({"role": "user", "content": user_message})

    try:
        ai_response = generate_ai_response(chat_history)
    except Exception as e:
        return jsonify(error=str(e)), 500

    user_chat_message = ChatMessage(username=current_user.username, message=user_message, is_user=True)
    ai_chat_message = ChatMessage(username='AI', message=ai_response, is_user=False)
    db.session.add(user_chat_message)
    db.session.add(ai_chat_message)
    db.session.commit()

    return jsonify(ai_response=ai_response)

@app.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', title='Profile', user=user)

@app.route("/edit_profile", methods=['GET', 'POST'])
@login_required
def edit_profile():
    form_birthday = EditBirthdayForm()
    form_gender_pronouns = EditGenderPronounsForm()

    if form_birthday.validate_on_submit():
        current_user.birth_date = form_birthday.birth_date.data
        current_user.is_profile_complete = True
        db.session.commit()
        flash('Your birthdate has been updated!', 'success')

    if form_gender_pronouns.validate_on_submit():
        current_user.gender = form_gender_pronouns.gender.data
        current_user.pronouns = form_gender_pronouns.pronouns.data
        db.session.commit()
        flash('Your gender and pronouns have been updated!', 'success')

    if request.method == 'GET':
        form_birthday.birth_date.data = current_user.birth_date
        form_gender_pronouns.gender.data = current_user.gender
        form_gender_pronouns.pronouns.data = current_user.pronouns

    return render_template('edit_profile.html', title='Edit Profile', form_birthday=form_birthday, form_gender_pronouns=form_gender_pronouns)

@app.route("/personality_test", methods=['GET', 'POST'])
@login_required
def personality_test():
    form = PersonalityForm()
    with open('questions.json') as f:
        questions = json.load(f)
    if form.validate_on_submit():
        for trait, question_pairs in questions.items():
            question_fields = [q for _, q in question_pairs]
            trait_score = sum(int(getattr(form, field).data) for field in question_fields)
            setattr(current_user, trait, trait_score)
        db.session.commit()
        flash('Your personality test is submitted!', 'success')
        return redirect(url_for('home'))
    return render_template('personality_test.html', title='Personality Test', form=form, questions=questions, enumerate=enumerate)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
