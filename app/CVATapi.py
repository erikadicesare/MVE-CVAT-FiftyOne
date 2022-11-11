from flask import request
import requests
import os, json
from pathlib import Path
import ntpath
import shutil
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('USERNAME_CVAT')
password = os.getenv('PASSWORD_CVAT')
url_cvat = os.getenv('URL_CVAT')

max_size_load_file = os.getenv('MAX_SIZE_LOAD_FILE')
credentials = {
    "username": username,
    "email": "",
    "password": password
}

login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
jsonObj = json.loads(login.text)
keyLogin = jsonObj['key']
print(keyLogin)

""""""
def uploadImages(id, name_task, files):
    uuid = request.form.get('uuid')
        
    pathFolder = 'temp{}'.format(uuid)

    # Check whether the specified path exists or not
    isExist = os.path.exists(pathFolder)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(pathFolder)

    dataTask = {
        "name": name_task + " #1",
        "project_id": int(id),
        "owner": 0,
        "assignee": 0,
        "overlap": 0,
        "segment_size": 150,
        "z_order": False,
        "image_quality": 100,
    }
    
    createEmptyTask = requests.post('{}/tasks'.format(url_cvat), data=dataTask, headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(createEmptyTask.text)
    taskId = jsonObj['id']
    print(taskId)
    
    ############################################################################################################################################
    
    # Salvo il primo file dentro static/data/projectCVAT per avere una immagine significativa per progetto (immagine presa dall'ultimo task inserito)
    #image = files
    #headfp, tailfp = ntpath.split(image[0].filename)
    #file_name, file_extension = ntpath.splitext(image[0].filename)
    #pathFirstFile = './app/static/data/projectCVAT/{}{}'.format(taskId, file_extension)
    #image[0].save(pathFirstFile)
    
    ############################################################################################################################################
    
    # Elimino il precedente file salvato per questo progetto (cerco i task e cerco gli id nella cartella static/data/projectCVAT)
    #prj = requests.get('http://localhost:8080/api/v1/projects/{}'.format(id), headers={"Authorization": f'Token {keyLogin}'})
    #jsonObj = json.loads(prj.text)
    #tasks_id = []
    #for t in jsonObj['tasks']:
    #    tasks_id.append(t['id'])
    #images_from_dir = os.listdir('./app/static/data/projectCVAT')
    #for ifd in images_from_dir:
    #    file_name, file_extension = ntpath.splitext(ifd)
    #    print(file_name, file_extension)
    #    print(tasks_id)
    #    if ((file_name in tasks_id) and (file_name!=tasks_id)):
    #        #img = "data/projectCVAT/{}{}".format(file_name, file_extension)
    #        print("immagine {} esistente".format(file_name))
    ############################################################################################################################################
    
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
            uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
            print(uploadImgs.text)

            fs = [pathFile]
            size = Path(pathFile).stat().st_size
            if (size!=0):
                countTask = countTask + 1
                dataTask['name']=name_task + " #"+str(countTask)
                createEmptyTask = requests.post('{}/tasks'.format(url_cvat), data=dataTask, headers={"Authorization": f'Token {keyLogin}'})
                jsonObj = json.loads(createEmptyTask.text)
                taskId = jsonObj['id']
    if (size>0): 
        images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
        uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
        print(uploadImgs.text)
    
    shutil.rmtree('temp{}'.format(uuid))

def create_project(name_project):

    dataProject = {
        "name": name_project
    }
    
    createProject = requests.post('{}/projects'.format(url_cvat), data=dataProject, headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(createProject.text)
    projectId = jsonObj['id']
    return projectId

def get_project(id_prj_MVE, id_prj_CVAT):
    prj = requests.get('{}/projects/{}'.format(url_cvat, id_prj_CVAT), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    img = "data/projectCVAT/notasks.png"
    nImages = 0
    if (len(jsonObj['tasks']) != 0):
        
        tasks_id = []
        for t in jsonObj['tasks']:
            tasks_id.append(t['id'])
            nImages = nImages+t['size']
        files = os.listdir('./app/static/data/projectCVAT')
        for file in files:
            file_name, file_extension = ntpath.splitext(file)
            print(file_name, file_extension, max(tasks_id))
            if (file_name==str(max(tasks_id))):
                img = "data/projectCVAT/{}{}".format(file_name, file_extension)
                
    project_info = {
        'id_MVE': id_prj_MVE,
        'id_CVAT': id_prj_CVAT,
        'name': jsonObj['name'],
        'nTask': len(jsonObj['tasks']),
        'nImages': nImages,
        'img': img
    }

    return(project_info)
