from flask import Flask, request, render_template, url_for, redirect
from flask_user import login_required, UserManager, current_user
import requests
import urllib.parse
import datetime
from models import db, User

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import translate as google_translate
import os

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

            
            return render_template(self.USER_EDIT_USER_PROFILE_TEMPLATE, form=form)


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

CRED_FILE = 'client_secret.json'
PROJECT_ID = "continual-block-413219"
TOKEN_FILE = 'token.json'
CREDENTIALS = None
SCOPES = ['https://www.googleapis.com/auth/cloud-translation', 
          'https://www.googleapis.com/auth/cloud-platform',
          'https://www.googleapis.com/auth/youtube.readonly']


if os.path.exists(TOKEN_FILE):
    CREDENTIALS = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

if not CREDENTIALS or not CREDENTIALS.valid:
    if CREDENTIALS and CREDENTIALS.expired and CREDENTIALS.refresh_token:
        CREDENTIALS.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CRED_FILE, SCOPES)
        flow.redirect_uri = 'http://localhost:37373/'
        CREDENTIALS = flow.run_local_server(port=37373)
            
            
    with open(TOKEN_FILE, 'w') as token:
        token.write(CREDENTIALS.to_json())

print("Credentials loaded successfully.")

def translate_text(text, lang):
    global CREDENTIALS, PROJECT_ID
    client = google_translate.TranslationServiceClient(credentials=CREDENTIALS)
    

    location = "global"

    parent = f"projects/{PROJECT_ID}/locations/{location}"

    text_lang_res = client.detect_language(
        content="Hello, world!",
        parent=parent,
        mime_type="text/plain",  # mime types: text/plain, text/html
    )

    text_lang = text_lang_res.languages[0].language_code

    # Detail on supported types can be found here:
    # https://cloud.google.com/translate/docs/supported-formats
    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": text_lang,
            "target_language_code": lang,
        }
    )

    return response.translations[0].translated_text


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

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    text = request.get_json()['text']
    lang = current_user.language

    result = translate_text(text, lang)
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
        response = requests.get(channel['endpoint'], headers={'Authorization': 'authkey ' + channel['authkey'], 'uid': str(current_user.id)})
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
                             headers={'Authorization': 'authkey ' + channel['authkey'], 'uid': str(current_user.id)},
                             json={'content': message_content, 'sender': message_sender, 'timestamp': message_timestamp})
    if response.status_code != 200:
        return "Error posting message: "+str(response.text), 400
    return redirect(url_for('show_channel')+'?channel='+urllib.parse.quote(post_channel))


# Start development web server
if __name__ == '__main__':
    app.run(port=5005, debug=True)
