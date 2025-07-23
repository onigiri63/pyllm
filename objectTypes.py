import time
from flask import json

class MessageList():
    def __init__(self):
        self.created = time.time()
        self.messages = []
        self.caption = ''

    def addMessage(self, sender, message):
        self.messages.append({'role': sender, 'content': message})

    def getJson(self):
        ret = '{\n'
        for index, message in enumerate(self.messages):
            role = f"role:{index+1}"  # Changed key to a unique integer
            content = f"content:{message['content']}"
            ret += f"{role}:{content}\n"
        ret += '}'
        return json.loads(ret)

    def getMessages(self):
        return self.messages
