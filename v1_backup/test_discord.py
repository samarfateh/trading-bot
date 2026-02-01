import requests
# Using the URL directly from your monitor.py file
DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1467339178701230122/MnWqFuFNUTO4HGMHfZA7eQEsZFjdGvUWIdA-WMb_jqiFVEtNkWpA85d93QaZ8FR6HkB2'

def test_connection():
    print(f"Testing Webhook: {DISCORD_WEBHOOK[:50]}...")
    
    data = {
        "content": "✅ **Integration Test**: The AMD Bot is successfully connected to specific channel."
    }
    
    try:
        r = requests.post(DISCORD_WEBHOOK, json=data)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
        
        if r.status_code == 204:
            print("SUCCESS: Message sent. Check your Discord channel!")
        else:
            print("FAILURE: Discord rejected the message.")
            
    except Exception as e:
        print(f"ERROR: Could not connect to internet or Discord. {e}")

if __name__ == "__main__":
    test_connection()
