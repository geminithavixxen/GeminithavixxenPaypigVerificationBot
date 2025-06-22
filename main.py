import tweepy
from flask import Flask
import threading, time, os
from datetime import datetime, timedelta

# Twitter API credentials (use Replit secrets)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

pending = {}
logfile = "verified_users.txt"

if not os.path.exists(logfile):
    open(logfile, "w").close()

def log_verified(user_id, username):
    ts = datetime.utcnow().isoformat()
    with open(logfile, "a") as f:
        f.write(f"{ts} - {username} ({user_id})\n")

initial_msg = (
    "👑 Tribute Protocol Initiated 👑\n\n"
    "1️⃣ Send a screenshot of your tribute.\n"
    "2️⃣ Then send a selfie holding a handwritten note:\n\n"
    "“I belong to Geminithavixxen” + your @username + today’s date.\n\n"
    "⏳ You have 2 hours to comply or be blocked. Obey."
)
warning_msg = "⚠️ 1 hour left. Submit tribute and verification selfie now or be blocked."
blocked_msg = "⛔ Verification failed. You are now blocked."

app = Flask(__name__)

@app.route("/")
def home():
    return "Geminithavixxen Verification Bot is running."

def check_dms():
    me = api.verify_credentials().id_str
    while True:
        try:
            dms = api.get_direct_messages(count=20)
            for dm in dms:
                sender = dm.message_create["sender_id"]
                if sender == me:
                    continue
                msg = dm.message_create["message_data"]
                text = msg.get("text", "")
                attach = msg.get("attachment", {})

                if sender not in pending:
                    api.send_direct_message(sender, initial_msg)
                    pending[sender] = {
                        "start": datetime.utcnow(),
                        "warned": False,
                        "tribute": False,
                        "selfie": False
                    }
                else:
                    if "I belong to Geminithavixxen" in text and str(datetime.now().day) in text:
                        pending[sender]["selfie"] = True
                    if attach.get("media"):
                        pending[sender]["tribute"] = True

                    if pending[sender]["tribute"] and pending[sender]["selfie"]:
                        user = api.get_user(user_id=sender)
                        api.send_direct_message(sender, "✅ You are verified. Obey.")
                        log_verified(sender, user.screen_name)
                        del pending[sender]
        except Exception as e:
            print("DM error:", e)
        time.sleep(60)

def monitor_users():
    while True:
        now = datetime.utcnow()
        for uid, data in list(pending.items()):
            elapsed = now - data["start"]
            if elapsed > timedelta(hours=2):
                try:
                    api.send_direct_message(uid, blocked_msg)
                    api.create_block(uid)
                except:
                    pass
                del pending[uid]
            elif elapsed > timedelta(hours=1) and not data["warned"]:
                try:
                    api.send_direct_message(uid, warning_msg)
                    pending[uid]["warned"] = True
                except:
                    pass
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=check_dms, daemon=True).start()
    threading.Thread(target=monitor_users, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
