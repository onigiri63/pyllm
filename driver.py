import tkinter as tk
from tkinter import scrolledtext
import threading
from graphing import DynamicPlot
import sys
from query import llmQuery
from PIL import Image, ImageDraw, ImageFont
import time
from runFromFile import runFromFile
from pyperclip import copy
# from markup import CodeSyntaxHighlighter

'''
 TODO: 
    -add a dropdown to select the model to run
    -minimze graphs properly on applicaion minimize
    -can we stop the prompt? (interrupt the subprocess)

'''
# format: file name, model name, context window size
# model = ('qwen2.5coder','qwen2.5-coder:7b', '2048')
# model = ('qwen2.5coder3b','qwen2.5-coder:3b', '2048')
# model = ('qwen2-32k','qwen2-32k', '2048')
model = ('llama3.2_32k','llama3.2_32k', '16384')


class LLMQueryUI:
    onlyCode = False
    def __init__(self):
        self.events = []
        self.breakout = [False]
        self.onlyCode = False
        self.initControls()

    def initControls(self):
        self.root = tk.Tk()
        # self.root.iconbitmap("iconTemplate@2x.gif")  # Set the icon for the window
        self.root.title("LLM Query Interface")
        self.root.geometry("1100x950")
        self.customfont = {"family": "Courier", "size": 10, "weight": "normal"}

        tk.Label(self.root, font=("Courier", 12), text="Enter your query:").pack(pady=5)

        self.entry = scrolledtext.ScrolledText(self.root, width=100, height=25, wrap=tk.WORD, font=("Courier", 10))
        self.entry.pack(pady=0, anchor=tk.NW)
        self.events.append((self.customfont,self.entry))
        
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=20, pady=0, fill=tk.BOTH, expand=True)
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=20)

        self.runButton = tk.Button(self.button_frame, bg="snow3", width=20, height=1, text="Run Query", font=("Courier", 10), command=self.on_button_click)
        self.runButton.grid(row=0, column=0, sticky="nsew")
        self.codeButton = tk.Button(self.button_frame, bg="snow3", width=20, height=1, text="CODE", font=("Courier", 10), command=self.codeOnly)
        self.codeButton.grid(row=0, column=1, sticky="nsew")
        self.copyButton = tk.Button(self.button_frame, bg="snow3", width=20, height=1, text="Paste Buffer", font=("Courier", 10), command=self.copyCode)
        self.copyButton.grid(row=0, column=2, sticky="nsew")
        self.countLabel = tk.Label(self.button_frame, font=("Courier", 10), height=1, text="context length: 0")
        self.countLabel.grid(row=0, column=3, sticky="nsew")

        self.output_text = scrolledtext.ScrolledText(self.root, width=100, height=25, wrap=tk.WORD, font=("Courier", 10))
        self.output_text.pack(pady=0, anchor=tk.NW)
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

        run = runFromFile(model)
        run.launch()
        # Start the GUI event loop
        self.root.mainloop()

    def on_button_click(self):
        # Reading the text from the input field
        user_input = self.entry.get("1.0",tk.END)
        thread = threading.Thread(target=self.runQuery,args=([user_input, self.callback]))
        thread.start()

    def runQuery(self, user_input, callback):
        self.output_text.delete(1.0, tk.END)  # Clear any text
        q = llmQuery(model)
        q.setQueryHeader(self.onlyCode)
        self.runButton.config(bg="green", text="Query In Progress")
        thread = threading.Thread(target=q.query_llm,args=([user_input.strip(), callback]))
        thread.start()
        thread.join()
        self.runButton.config(bg="snow3", text="Run Query")
        
    def callback(self, responses):
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

    def get_font_dims(self, font):
        # Create an image with a blank white background
        width, height = 100, 100
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        # Load the font and measure its size
        pil_font = ImageFont.truetype("cour.ttf", font["size"])

        # Use textbbox to get the bounding box
        bbox = draw.textbbox((0, 0), "A", font=pil_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        return (text_width, text_height)

    def resize_textboxes(self, font, control):
        text_width = int( (self.root.winfo_width() - 250) / (self.get_font_dims(font)[0] + 2) )
        text_height = int( self.root.winfo_height() / (6 * self.get_font_dims(font)[1]) )
        
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
        while not self.breakout[0]:
            q = llmQuery(model)
            q.setQueryHeader(self.onlyCode)
            try:
                user_input = self.entry.get("1.0",tk.END)
                count = str(q.get_context_length(user_input))
                callback(count)
            except:
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

if __name__ == "__main__":
    llm_query_ui = LLMQueryUI()