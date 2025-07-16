import subprocess
import time
from PIL import Image, ImageDraw, ImageFont
import docker

def get_font_dims(font):
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

def blockForDocker():
    while True:
        try:
            # Use 'docker ps -a' command to list all containers, including stopped ones
            output = subprocess.check_output(['docker', 'ps', '-a'])
            
            # If the command is successful and returns a non-empty output, then Docker daemon is running
            if 'CONTAINER ID' in output.decode('utf-8'):
                print("Docker daemon is running.")
                return True
            
            # If an error occurs or no output is returned, Docker daemon is not running
            else:
                time.sleep(1)  # Wait before retrying
                continue
    
        except subprocess.CalledProcessError as e:
            time.sleep(1)  # Wait before retrying
            continue

        except Exception as e:
            time.sleep(1)  # Wait before retrying
            continue

def check_docker_engine():
    try:
        print("Checking docker engine")
        client = docker.from_env()
        return True
    except Exception as e:
        print(f"Docker engine is not running, starting...")
        startDockerEngine()
        return False
    
def startDockerEngine(self):
        # Run the executable
    result = subprocess.run([f'%PROGRAMFILES%\\Docker\\Docker\\Docker Desktop.exe', '-D'], shell=True)
    blockForDocker()

    # Check if the return code is 0 (success)
    if result.returncode == 0:
        print("Docker engine launched!")
    else:
        print(f"Error running docker, you must have docker engine installed to run this program.")
        exit()
