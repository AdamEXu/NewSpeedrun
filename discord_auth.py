from flask import redirect, request, session
import requests
import os

CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
API_BASE_URL = "https://discord.com/api"
AUTHORIZATION_BASE_URL = API_BASE_URL + "/oauth2/authorize"
TOKEN_URL = API_BASE_URL + "/oauth2/token"
USER_URL = API_BASE_URL + "/users/@me"

def get_discord_login_url():
    # return "https://discord.com/oauth2/authorize?client_id=1268238234341609515&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fcallback&scope=guilds+identify+email+guilds.join"
    return f"{AUTHORIZATION_BASE_URL}?response_type=code&client_id={CLIENT_ID}&scope=identify&redirect_uri={REDIRECT_URI}&prompt=consent"

def get_token(code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify',
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    return response.json()

def get_user_info(token):
    headers = {
        'Authorization': f"Bearer {token}"
    }
    response = requests.get(USER_URL, headers=headers)
    return response.json()

BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

def assign_role(guild_id, user_id, role_id):
    url = f"{API_BASE_URL}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        'Authorization': f"Bot {BOT_TOKEN}",
        'Content-Type': 'application/json'
    }
    response = requests.put(url, headers=headers)
    return response.status_code