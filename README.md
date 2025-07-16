## A Python tkinter interface for ollama LLM queries.
* Features include real time memory and cpu plotting, a code-only button, a context length counter, and a paste button.
* Requires docker desktop, Windows, Python

NO models are committed here!  You can obtain them from https://ollama.com/search



### Download the repository:
```
git clone https://github.com/onigiri63/pyllm.git
cd pyllm
```

### Install the python requirements
```
pip install -r requirements.txt
```

### Run the program
```
python driver.py
```
### To change the model, do the following:
### Run the container using the model llama3.2:

Run aihelper in detached mode, take note of container id
```
docker run -p 11434:11434 -d ailtire/aihelper:llama3.2
```
#### Optional (enable gpu resources access)
```
docker run --gpus all --cpus 22 -p 11434:11434 -t ailtire/aihelper:llama3.2 nvidia-smi
```

### To use a different model:

Grab container id and copy the certificate into the container
```
docker ps 
docker cp certificate.crt ${container_id}:/usr/local/share/ca-certificates/
```

Launch terminal in root mode while container is running
```
docker exec -u root -t -i ${container_id} /bin/bash
```

Refresh the certificate store 
```
update-ca-certificates
```


### The following commands will load your container with your chosen model
```
docker restart ${container_id}
docker exec -u root -t -i ${container_id} /bin/bash
ollama pull <your model here>
exit
```

### Optional:  increase the context size for a net

#### the input token limit for ollama seems to default to 2k - increasing this WILL increase memory demand!
'''
docker exec -u root -t -i ${container_id} /bin/bash
ollama run <llm name>
/set parameter num_ctx <your context size>
/bye
exit
'''
This will ONLY increase the context for the running container - if you want to permanently increase the length,
follow the instructions below to create and store a permanent image.

### Optional:  Store the altered model locally as a new image
Now run the file createContainerImg.bat, make sure you record the file name.  Store the file in the downloaded repository folder ollama/models.
FOR NOW, you can add the model to the tuple at the beginning of driver.py, in the format:
```
      model = (<model name>,<file name>,<context length>)
```
* The model name is the name from the ollama models website
* The file name is the name you gave the file in createContainerImg.bat
* The context length is the value obtained from the details when you click the model on the ollama website. 


 TODO: 
* add a dropdown to select the model to run
* can we do more to automate the container setup?
* automate the process of creating images with new models
