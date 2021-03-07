from flask import Flask, render_template, session, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
from threading import Thread
from flask_migrate import Migrate
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = "hard to guess"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

app.config['MAIL_SUBJECT_PREFIX'] = '[NEW MESSAGE]-'
app.config['MAIL_SENDER'] = 'ADMIN <shanoorahmedhojai@gmail.com>'
app.config['ADMIN'] = os.environ.get('ADMIN')

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app,db)

def send_mail_async(app,msg):
    with app.app_context():
        mail.send(msg)

def send_mail(to,subject,template,**kwargs):
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + subject,sender=app.config['MAIL_SENDER'],recipients = [to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_mail_async, args=[app,msg])
    thr.start()
    return thr

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(25))
    email = db.Column(db.String(25))
    phone = db.Column(db.Integer)
    subject = db.Column(db.String(25))
    message = db.Column(db.String(100))
    def __repr__(self):
        return '< User %r>' % self.username

class ContactForm(FlaskForm):
    name = StringField('Name',validators = [DataRequired()])
    email = StringField('Email',validators = [DataRequired()])
    phone = StringField('Phone',validators = [DataRequired()])
    subject = StringField('Subject',validators = [DataRequired()])
    message = TextAreaField('Message',validators = [DataRequired()])   
    submit = SubmitField('Send')

@app.route("/",methods=['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        user = User(name = form.name.data, email = form.email.data, phone = form.phone.data, subject = form.subject.data, message = form.message.data)
        db.session.add(user)
        db.session.commit()
        if app.config['ADMIN']:
            send_mail(app.config['ADMIN'], form.subject.data, 'mail/new_user', user = user)
            flash('Thank You! Your message has been sent.')
            return redirect(url_for('contact'))
    return render_template('contact.html',form=form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'),500

@app.shell_context_processor
def make_shell_context():
    return dict(db=db,User=User)