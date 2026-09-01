import requests

BOT_TOKEN = "8382522427:AAEXhvPzou4e5mjDvYVlG1KFrrBhi1VeEUY"
CHAT_ID = "382132899"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "📱 Sent from phone Python test!"
}

r = requests.post(url, data=data)
print(r.text)