from flask import Flask, request, render_template, url_for, redirect
from flask_user import login_required, UserManager, current_user
import requests
import urllib.parse
import datetime
from models import db, User

from google_api_functions import *

SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'French', 'de': 'German', 'fa': 'Persian'}
CREDENTIALS = None

class CustomUserManager(UserManager):
    @login_required
    def edit_user_profile_view(self):
            # Initialize form
            form = self.EditUserProfileFormClass(request.form, obj=current_user)

            # Process valid POST
            if request.method == 'POST' and form.validate():
                # Update fields
                form.populate_obj(current_user)

                # Save object
                self.db_manager.save_object(current_user)
                self.db_manager.commit()

                return redirect(self._endpoint_url(self.USER_AFTER_EDIT_USER_PROFILE_ENDPOINT))

            # Render form
            self.prepare_domain_translations()

            user_lang = current_user.language

            
            return render_template(self.USER_EDIT_USER_PROFILE_TEMPLATE, form=form, language_list=SUPPORTED_LANGUAGES, language=user_lang)


class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Messenger"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

    USER_AFTER_REGISTER_ENDPOINT = 'home_page'
    USER_AFTER_CONFIRM_ENDPOINT = 'home_page'
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'


app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = CustomUserManager(app, db, User)  # initialize Flask-User management

HUB_AUTHKEY = '1234567890'
HUB_URL = 'http://localhost:5555'

CHANNELS = None
LAST_CHANNEL_UPDATE = None




def update_channels():
    global CHANNELS, LAST_CHANNEL_UPDATE
    if CHANNELS and LAST_CHANNEL_UPDATE and (datetime.datetime.now() - LAST_CHANNEL_UPDATE).seconds < 60:
        return CHANNELS
    # fetch list of channels from server
    response = requests.get(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY})
    if response.status_code != 200:
        return "Error fetching channels: "+str(response.text), 400
    channels_response = response.json()
    if not 'channels' in channels_response:
        return "No channels in response", 400
    CHANNELS = channels_response['channels']
    LAST_CHANNEL_UPDATE = datetime.datetime.now()
    return CHANNELS


@app.route('/')
def home_page():
    # fetch list of channels from server
    return render_template("home.html", channels=update_channels())

@app.route('/load_creds')
def load_creds():
    global CREDENTIALS
    CREDENTIALS = set_credentials(CREDENTIALS, 'token_1.json', 'cred_1.json')
    return "Credentials loaded successfully."

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    text = request.get_json()['text']
    lang = current_user.language

    result = translate_text(text, lang, CREDENTIALS)
    return {'translation':result}, 200
        

@app.route('/show')
def show_channel():
    # fetch list of messages from channel
    show_channel = request.args.get('channel', None)
    if not show_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(show_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404
    if isinstance(current_user, User):
        response = requests.get(channel['endpoint'], headers={
                                                        'Authorization': 'authkey ' + channel['authkey'], 
                                                        'uid': str(current_user.id), 
                                                        'password': current_user.password})
        if response.status_code != 200:
            return "Error fetching messages: "+str(response.text), 400
        messages = response.json()
        return render_template("channel.html", channel=channel, messages=messages)
    else:
        return redirect(url_for('user.login'))
    
@app.route('/user/lang_update', methods=['POST'])
@login_required
def lang_update():
    # send message to channel
    lang = request.get_json()['language']
    current_user.language = lang
    db.session.commit()
    return {'message':'ok'}, 200

@app.route('/post', methods=['POST'])
def post_message():
    # send message to channel
    post_channel = request.form['channel']
    if not post_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(post_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404
    message_content = request.form['content']
    if not current_user.first_name and not current_user.last_name:
        message_sender = current_user.username
    else:
        message_sender = f"{current_user.first_name} {current_user.last_name}" 
    message_timestamp = datetime.datetime.now().isoformat()
    response = requests.post(channel['endpoint'],
                             headers={
                                 'Authorization': 'authkey ' + channel['authkey'], 
                                 'uid': str(current_user.id), 
                                 'password': current_user.password},
                             json={'content': message_content, 'sender': message_sender, 'timestamp': message_timestamp})
    if response.status_code != 200:
        return "Error posting message: "+str(response.text), 400
    return redirect(url_for('show_channel')+'?channel='+urllib.parse.quote(post_channel))


# Start development web server
if __name__ == '__main__':
    app.run(port=5005, debug=True)
