from flask import Flask, redirect, request, render_template
import requests
import os

app = Flask(__name__)

# Konfigurasi Discord
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
WEBHOOK_URL = "https://discord.com/api/webhooks/1394009935544586313/aDTLxKzvh8ouaV6B_OpaZ42dQtuiNfCRuJsCgZI55YAztbGMNwJQ1NSiOPjRp7UTw0W1"

OAUTH_SCOPE = "identify guilds.join"
DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_URL = "https://discord.com/api"

@app.route("/")
def index():
    auth_url = (
        f"{DISCORD_AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={OAUTH_SCOPE}"
    )
    return render_template("index.html", auth_url=auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect("/error")

    # Tukar kode dengan access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": OAUTH_SCOPE,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_res = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    if token_res.status_code != 200:
        return redirect("/error")

    token_json = token_res.json()
    access_token = token_json["access_token"]

    # Ambil data user
    user_res = requests.get(
        f"{DISCORD_API_URL}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if user_res.status_code != 200:
        return redirect("/error")
    user = user_res.json()

    # Tambahkan user ke server
    member_res = requests.put(
        f"{DISCORD_API_URL}/guilds/{GUILD_ID}/members/{user['id']}",
        headers={
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"access_token": access_token}
    )

    # Kirim notifikasi ke webhook
    requests.post(WEBHOOK_URL, json={
        "embeds": [
            {
                "title": "🎉 User Baru Bergabung!",
                "description": f"**{user['username']}#{user['discriminator']}** berhasil join server.",
                "color": 0x00FF7F,
                "thumbnail": {
                    "url": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"
                },
            }
        ]
    })

    if member_res.status_code in (200, 201, 204):
        return render_template("success.html")
    else:
        return redirect("/error")

@app.route("/error")
def error():
    return render_template("error.html")

if __name__ == "__main__":
    app.run(debug=True)
