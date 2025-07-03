### A Python tkinter interface for ollama LLM queries.
* Features include real time memory and cpu plotting, a code-only button, a context length counter, and a paste button.
* Requires docker desktop, Windows

NO models are committed here!  You can obtain them from https://ollama.com/search

To download the repository, use:
```
git clone https://github.com/onigiri63/pyllm.git
cd pyllm
```


To create a container from a model, first follow these instructions:

Run aihelper in detached mode, take note of container id
```
docker run -p 11434:11434 -d ailtire/aihelper:llama3.2
```

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

Optional (enable gpu resources access)
```
docker run --gpus all --cpus 22 -p 11434:11434 -t ailtire/aihelper:llama3.2 nvidia-smi
```

On windows wsl Docker, container logs are stored in 
```
"\\wsl.localhost\docker-desktop\tmp\docker-desktop-root\var\lib\docker\containers\"
```

The following commands will load your container with your chosen model
```
docker restart ${container_id}
docker exec -u root -t -i ${container_id} /bin/bash
ollama pull <your model here>
exit
```

Now run the file createContainerImg.bat, make sure you record the file name.  Store the file in the downloaded repository folder ollama/models.
FOR NOW, you can add the model to the tuple at the beginning of driver.py, in the format:
```
      model = (<model name>,<file name>,<context length>)
```
where the model name is the name from the ollama models website, the file name is the name you gave the file in createContainerImg.bat, and the context length is the value obtained from the details when you click the model on the ollama website. 

```
 TODO: 
    -add a dropdown to select the model to run
    -minimize graphs properly when you minimize the application
    -can we stop the prompt? (interrupt the subprocess)
    -labels for the graphs
    -can we do more to automate the container setup?
```
