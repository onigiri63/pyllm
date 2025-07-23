import os
import time

from flask import json

class saveHistory:
    def __init__(self, savedir):
        self.savedir = savedir
        self.created = str(time.time()).split('.')[0]
        self.filename = f"{self.savedir}\\{self.created}"
        self.startSave()
    
    def startSave(self):
        output = ''
        try:
            f =  open(self.filename, "w")
            output += '{' +f"\"created\": \"{self.created}\","\
            "\"messages\": []}"
            f.write(output)
            f.close()

            print("Chat history started")
        except Exception as e:
            print(f"An error occurred while saving chat history: {e}")
    
    def addMessage(self, message, role):
        try:
            fa = open(self.filename,'r')
            read = fa.read()
            fa.close()
            curContent = json.loads(read)

            f = open(self.filename, "w")
            outmessage = message.replace("\"","\"").replace('\n','\\n')
            comma = ''
            if len(curContent['messages']) > 0:
                comma = ','
            newMessage = comma + '{' + f"\"role\": \"{role}\", \"content\": \"{outmessage}\"" + '}'
            curContent['messages'].append(newMessage)
            f.write(json.dumps(curContent))
            f.close()

            print("message saved successfully.")
        except Exception as e:
            print(f"An error occurred while saving chat history: {e}")

    def loadChat(self, filename):
        file = open(f"{self.savedir}\\{filename}", "r").read()
        myjson = json.loads(file)
        ret = [myjson['messages']]
        return ret
    
    def enumerateChats(self):
        ret = []
        for file in os.listdir(self.savedir):
            ret.append(file)
        return ret

