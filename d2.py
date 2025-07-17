import tkinter as tk
from tkinter import scrolledtext
import threading
from chat import llmChat
from graphing import DynamicPlot
import sys
import helpers
import time
from runFromFile import runFromFile
from pyperclip import copy
# from markup import CodeSyntaxHighlighter

'''
 TODO: 
    -add a dropdown to select the model to run
'''
# format: file name, model name, context window size
# model = ('qwen2.5coder','qwen2.5-coder:7b', '2048')
# model = ('qwen2.5coder3b','qwen2.5-coder:3b', '2048')
# model = ('qwen2-32k','qwen2-32k', '2048')
model = ('llama3.2_32k','llama3.2_32k', '16384')

class LLMQueryUI:
    onlyCode = False
    def __init__(self):
        helpers.check_docker_engine()
        self.events = []
        self.breakout = [False]
        self.onlyCode = False
        self.minimized = False
        self.chat = llmChat(model)
        self.initControls()
        runFromFile(model).launch()
        buttonthread = threading.Thread(target=self.buttonStatus, args=([self.breakout]))
        buttonthread.daemon = True
        buttonthread.start()
        self.root.mainloop()

    def minimize(self):
        if self.minimized:
            return
        self.minimized = True
        self.cpuplot.minimize()
        self.memplot.minimize()
    
    def maximize(self):
        if not self.minimized:
            return
        self.minimized = False
        self.cpuplot.maximize()
        self.memplot.maximize()

    def stopLLM(self):
        self.chat.stopGeneration()

    def initControls(self):
        self.root = tk.Tk()
        # self.root.iconbitmap("iconTemplate@2x.gif")  # Set the icon for the window
        self.root.title("LLM Query Interface")
        self.root.geometry("1100x950")
        self.root.minsize(1100, 300) # sets the minimum size of the root window
        self.customfont = {"family": "Courier", "size": 10, "weight": "normal"}

        tk.Label(self.root, font=("Courier", 12), text="Enter your query:").pack(pady=5)

        self.entry = scrolledtext.ScrolledText(self.root, width=100, height=25, wrap=tk.WORD, font=("Courier", 10))
        self.entry.pack(pady=0, anchor=tk.NW)
        self.events.append((self.customfont,self.entry))
        
        self.frame = tk.Frame(self.root, height=1)
        self.frame.pack(padx=0, pady=0, fill=tk.BOTH, anchor=tk.NW)
        self.button_frame = tk.Frame(self.frame, relief=tk.RIDGE, height=1)
        self.button_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=0)

        self.runButton = tk.Button(self.button_frame, bg="snow3", width=17, height=1, text="Run Query", font=("Courier", 10), command=self.on_button_click)
        self.runButton.grid(row=0, column=0, sticky="nsew")
        self.stopButton = tk.Button(self.button_frame, bg="snow3", width=17, height=1, text="Stop Query", font=("Courier", 10), command=self.stopLLM)
        self.stopButton.grid(row=0, column=1, sticky="nsew")
        self.codeButton = tk.Button(self.button_frame, bg="snow3", width=17, height=1, text="CODE OFF", font=("Courier", 10), command=self.codeOnly)
        self.codeButton.grid(row=0, column=2, sticky="nsew")
        self.copyButton = tk.Button(self.button_frame, bg="snow3", width=17, height=1, text="Paste Buffer", font=("Courier", 10), command=self.copyCode)
        self.copyButton.grid(row=0, column=3, sticky="nsew")
        self.countLabel = tk.Label(self.button_frame, font=("Courier", 10), height=1, text="context length: 0")
        self.countLabel.grid(row=0, column=4, sticky="nsew")

        self.output_text = scrolledtext.ScrolledText(self.root, width=100, height=27, wrap=tk.WORD, font=("Courier", 10))
        self.output_text.pack(pady=0, anchor=tk.NW, fill=tk.Y, expand=True)
        self.events.append( (self.customfont, self.output_text))
        
        cpuoffsetX = 600
        cpuoffsetY = 0
        self.cpuplot = DynamicPlot('CPU % Usage', '0', '100', cpuoffsetX, cpuoffsetY, self.root, self.breakout)

        memoffsetX = 0
        memoffsetY = 300
        self.memplot = DynamicPlot('Memory % Usage', '0', '100', memoffsetX, memoffsetY, self.root, self.breakout)

        tokenThread = threading.Thread(target=self.tokenCounterThread, args = ([self.tokenCallBack]))
        tokenThread.daemon = True  # Ensure the thread exits when the main program exits
        tokenThread.start()

        self.root.bind("<Configure>", lambda event:self.bindResize(event))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.onclosing(self.onclosing(self.breakout)))

        resizeThread = threading.Thread(target=self.on_configure )
        resizeThread.daemon = True
        resizeThread.start()

    def on_button_click(self):
        # Reading the text from the input field
        user_input = self.entry.get("1.0",tk.END)
        thread = threading.Thread(target=self.runQuery,args=([user_input, self.responseCallback]))
        thread.start()

    def buttonStatus(self, breakout):
        while not breakout[0]:
            if self.chat.queryInProgress:
                self.runButton.config(bg="green", text="Query In Progress")
            else:
                self.runButton.config(bg="snow3", text="Run Query")
            time.sleep(0.5)

    def runQuery(self, user_input, callback):
        self.output_text.delete(1.0, tk.END)  # Clear any text
        self.chat.setQueryHeader(self.onlyCode)
        self.chat.send_chat(user_input.strip(), callback)
        
    def responseCallback(self, responses):
        self.output_text.insert(tk.END, responses) 
        self.output_text.see(index=tk.END)

    def onclosing(self, breakout: list):
        breakout[0] = True
        print("Exiting application...")
        try:
            if self.root is not None:
                self.root.destroy()
            if self.cpuplot is not None:
                self.cpuplot.destroy()
            if self.memplot is not None:
                self.memplot.destroy()
            sys.exit()
        except Exception as e:
            print(f"Error during closing: {e}")

    def resize_textboxes(self, font, control):
        text_width = int( (self.root.winfo_width() - 250) / (helpers.get_font_dims(font)[0] + 2) )
        text_height = int( self.root.winfo_height() / (6 * helpers.get_font_dims(font)[1]) )
        
        control.config(width=text_width, height=text_height)

    def bindResize(self, event):
        self.resize_textboxes(self.customfont, self.entry)
        self.resize_textboxes(self.customfont, self.output_text)

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        cpuoffsetX = root_w - 250
        cpuoffsetY = 20
        self.cpuplot.updatePosition(cpuoffsetX, cpuoffsetY, root_x, root_y, root_h)
        self.cpuplot.after(10, self.cpuplot.lift)
        memoffsetX = root_w - 250
        memoffsetY = int(root_h / 2)
        self.memplot.updatePosition(memoffsetX, memoffsetY, root_x, root_y, root_h)
        self.memplot.after(10,self.memplot.lift)

    def tokenCounterThread(self, callback):
        oldcount = 0
        while not self.breakout[0]:
            try:
                user_input = self.entry.get("1.0",tk.END)
                count = helpers.get_context_length(user_input)
                count += self.chat.tokenCount()
                if count != oldcount:
                    oldcount = count
                    callback(str(count))
            except Exception as e:
                print(f"error: {e}")
                pass
            time.sleep(.5)

    def tokenCallBack(self, new_text):
        if self.countLabel is not None:
            self.countLabel.config(text="context length: " + new_text + " of "+ model[2])  # Update the label's with the new text

    def codeOnly(self):
        self.onlyCode = not self.onlyCode
        if self.onlyCode:
            self.codeButton.config(bg="green", text="CODE ON")
        else:
            self.codeButton.config(bg="snow3", text="CODE OFF")

    def copyCode(self):
        copy(self.output_text.get("1.0",tk.END))
    
    def on_configure(self):
        while True:
            state = self.root.state()
            if state == "iconic":  # Minimized
                self.minimize()
            elif state == "zoomed":  # Maximized
                self.maximize()
            elif state == "normal":  # Restored
                self.maximize()
            time.sleep(.1)

if __name__ == "__main__":
    llm_query_ui = LLMQueryUI()