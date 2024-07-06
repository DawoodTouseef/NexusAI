"""
import requests

messages=[]
while True:
    user_input=input("Enter the message:")
    if "exit" in user_input:
        break
    messages.append({"role": "user", "content": user_input})
    req=requests.post("http://localhost:5000/chat/",json={"messages":messages})
    print(req.json()['message'])
    messages.append({"role": "user", "content": req.json()['message']})



"""
