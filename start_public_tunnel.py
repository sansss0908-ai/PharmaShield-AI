import time
from pyngrok import ngrok

try:
    public_url = ngrok.connect(5002)
    print("\n=========================================")
    print(f"🚀 PUBLIC SMARTPHONE APP URL: {public_url}")
    print("=========================================\n")
    
    with open("public_url.txt", "w") as f:
        f.write(str(public_url))
        
    while True:
        time.sleep(10)
except Exception as e:
        print(f"Error starting tunnel: {e}")
