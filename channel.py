## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify, redirect
import json
import requests

from models import db, Post, MediaLink

from google_api_functions import PROJECT_ID, extract_media, set_credentials


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary

CREDENTIALS = None
HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Movie & Music Talk"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

@app.route('/load_creds')
def load_creds():
    global CREDENTIALS
    CREDENTIALS = set_credentials(CREDENTIALS, 'token_2.json', 'cred_2.json')
    return "Credentials loaded successfully."

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    save_message(message)

    return "OK", 200

def read_messages():
    posts = Post.query.all()
    messages = []
    for post in posts:
        media_links = {}
        for m in post.media_links:
            media_links[m.name] =m.link
        
        message = {'sender': post.username,
                   'content': post.content,
                   'timestamp': post.posted_at.strftime('%a %d %b %Y, %I:%M%p'),
                   'media_links': media_links}
        messages.append(message)
    return messages


def save_message(message):
    message_media = extract_media(message['content'], CREDENTIALS)
    if message['sender']:
        message_obj = Post(username=message['sender'], content=message['content'])
    else:
        message_obj = Post(content=message['content'])
    db.session.add(message_obj)
    db.session.commit()
    for m in message_media:
        media_links_obj= MediaLink(post_id=message_obj.id, name=m, link=message_media[m])
        db.session.add(media_links_obj)
    db.session.commit()

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
