from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import translate as google_translate
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import os

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

def extract_media(message):
    global CREDENTIALS, PROJECT_ID
    vertexai.init(credentials=CREDENTIALS, project= PROJECT_ID)
    model = GenerativeModel("gemini-pro")
    responses = model.generate_content(
        f"""extract any movie or song names from this message. 
        if it's a movie attach ' trailer' to the movie name.
        finally list them as csv or return '' if there is none. '{message}'""",
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0.9,
            "top_p": 1
        },
        safety_settings=[],
        stream=True,
    )
    res = ""
    for response in responses:
        if response.text:
            res+=response.text

    if res=="''":
        return {}

    media_names = res.split(",")
    api_service_name = "youtube"
    api_version = "v3"

    youtube = build(api_service_name, api_version, credentials=CREDENTIALS)

    media = {}
    for m in media_names:
        request = youtube.search().list(part="snippet",
                maxResults=1,
                q=m)
        response = request.execute()

        link = f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
        title = response['items'][0]['snippet']['title']
        media[title] = link
    return media
