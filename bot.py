import os
import time
import requests
import agent
import homelab

API = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}"
MY_CHAT = int(os.environ["TELEGRAM_CHAT_ID"])


def get_updates(offset):
    r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=40)
    r.raise_for_status()
    return r.json()["result"]


def send_message(chat_id, text):
    r = requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    r.raise_for_status()


def send_typing(chat_id):
    # Shows "typing..." in Telegram while the agent thinks
    requests.post(f"{API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=10)


def status_text():
    lines = ["VMs:"]
    for vm in homelab.get_vms():
        lines.append(("🟢 " if vm["on"] else "🔴 ") + vm["name"])
    lines.append("\nContainers:")
    for c in homelab.get_containers():
        lines.append(("🟢 " if c["running"] else "🔴 ") + f"{c['name']} ({c['host']})")
    return "\n".join(lines)


def ask_agent(question):
    try:
        return agent.ask(question)
    except Exception as e:
        # Never let an AI problem crash the bot; print only the error type
        print(f"Agent error ({type(e).__name__})")
        return "AI is not available right now (is the SSH tunnel open?). /status still works."


def main():
    offset = None
    print("Bot is running. Ctrl+C to stop.")
    while True:
        try:
            for update in get_updates(offset):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                if message.get("chat", {}).get("id") != MY_CHAT:
                    continue
                text = message.get("text", "")
                if text.startswith("/status"):
                    send_message(MY_CHAT, status_text())
                elif text:
                    send_typing(MY_CHAT)
                    send_message(MY_CHAT, ask_agent(text))
        except requests.RequestException as e:
            # Print only the error type: the full message includes the URL with the token
            print(f"Network error ({type(e).__name__}), retrying in 10 seconds")
            time.sleep(10)


if __name__ == "__main__":
    main()
