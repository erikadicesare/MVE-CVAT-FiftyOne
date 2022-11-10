from flask import request
import requests
import os, json
from pathlib import Path
import ntpath
import shutil

max_size_load_file = os.getenv('MAX_SIZE_LOAD_FILE')

def uploadImages(username, password, name_task, files):
    uuid = request.form.get('uuid')
        
    pathFolder = 'temp{}'.format(uuid)

    # Check whether the specified path exists or not
    isExist = os.path.exists(pathFolder)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(pathFolder)

    credentials = {
        "username": username,
        "email": "",
        "password": password
    }
    
    login = requests.post('http://localhost:8080/api/v1/auth/login', json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    dataTask = {
        "name": "my task #1",
        "project_id": 10,
        "owner": 0,
        "assignee": 0,
        "overlap": 0,
        "segment_size": 150,
        "z_order": False,
        "image_quality": 100,
    }
    
    createEmptyTask = requests.post('http://localhost:8080/api/v1/tasks', data=dataTask, headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(createEmptyTask.text)
    taskId = jsonObj['id']
    
    #files = request.files.getlist('fileList')
    fs = []
    size = 0 
    totalSize = 0
    countTask = 1

    for file in files:
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        file.save(pathFile)
        totalSize = totalSize + Path(pathFile).stat().st_size
    
    #nTasks = round_up(totalSize/int(max_size_load_file))
    
    for file in files:
        
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        
        size = size + Path(pathFile).stat().st_size
        if (size<int(max_size_load_file)):
            fs.append(pathFile)
        else:
            images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
            uploadImgs = requests.post('http://localhost:8080/api/v1/tasks/{}/data'.format(taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})

            print(uploadImgs.text)
            fs = [pathFile]
            size = Path(pathFile).stat().st_size
            if (size!=0):
                countTask = countTask + 1
                dataTask['name']=name_task + " #"+str(countTask)
                createEmptyTask = requests.post('http://localhost:8080/api/v1/tasks', data=dataTask, headers={"Authorization": f'Token {keyLogin}'})
                jsonObj = json.loads(createEmptyTask.text)
                taskId = jsonObj['id']
    if (size>0):   
        images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
        uploadImgs = requests.post('http://localhost:8080/api/v1/tasks/{}/data'.format(taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
        print(uploadImgs.text)
    
    shutil.rmtree('temp{}'.format(uuid))