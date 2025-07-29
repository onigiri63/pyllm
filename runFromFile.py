import subprocess

class runFromFile():
    def __init__(self, model):
        self.model = model

    def kill_existing_containers(self):
        self.run_command(['docker', 'container', 'prune', '-f'])

    # to run a shell command and capture its output
    def run_command(self, command):
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

    # Check if the image already locally
    def check_image_exists(self):
        try:
            output, _ = self.run_command(['docker', 'images'])
            return self.model[0] in output
        except subprocess.CalledProcessError:
            return False

    # Load the Docker image if it does not exist locally
    def load_image(self):
        print(f'loading docker image from file {self.model[0]}.tar.  This might take a while on the first run, please be patient!')
        try:
            self.run_command(['docker', 'load', '-i', f'models/{self.model[0]}' + ".tar"])
            print("Docker image loaded successfully.")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Failed to load Docker image: {e}")
            return -1
    
    def check_container_running(self):
        try:
            output, _ = self.run_command(['docker', 'ps'])
            return self.model[0] in output
        except subprocess.CalledProcessError:
            return False

    # Run a container using the loaded image if it exists, otherwise just run_command will handle the error
    def run_container(self):
        print(f'launching container')
        try:
            self.run_command(['docker', 'run', '-p', '11434:11434', '--memory=\"6g\"' '-d', self.model[0]] )
            # self.run_command(['docker', 'run', '--memory=\"16g\"', '--shm-size=\"16g\"','-p', '11434:11434', '-d', self.model[0]] )
        except subprocess.CalledProcessError as e:
            print(f"Failed to run Docker container: {e}")
            return -1

    def launch(self):
        if self.check_image_exists():
            print("Docker image already exists, running container from existing image.")    
        else:
            self.load_image()
        
        self.kill_existing_containers()
        if not self.check_container_running():
            print("No existing container running, starting a new one.")
            self.run_container()
        else:
            print("Container is already running, using existing container.")

if __name__ == "__main__":
    run = runFromFile('qwen2.5.coder')
    run.launch()