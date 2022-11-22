from zipfile import ZipFile
from flask import request
import requests
import os, json
from pathlib import Path
import ntpath
import shutil
from PIL import Image  
from app import dbquery
import PIL  
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


def uploadImages(id, name_task, files):

    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    uuid = request.form.get('uuid')
        
    pathFolder = 'temp{}'.format(uuid)

    # controllo se la cartella esiste 
    isExist = os.path.exists(pathFolder)
    
    # creo la cartella se non esiste
    if not isExist:
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
    
    fs = []
    size = 0 
    totalSize = 0
    countTask = 1
    idMVE = dbquery.get_projectCVAT(id)[0]

    for file in files:
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        file.save(pathFile)
        totalSize = totalSize + Path(pathFile).stat().st_size
    
    for file in files:
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        
        size = size + Path(pathFile).stat().st_size
        if (size<int(max_size_load_file)):
            fs.append(pathFile)
            dbquery.insert_MVSxCVAT_row(tailfp, idMVE, taskId)
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
                dbquery.insert_MVSxCVAT_row(tailfp, idMVE, taskId)
    if (size>0): 
        images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
        uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
        print(uploadImgs.text)

    ############################################################################################################################################################################
    
    # Salvo il primo file dentro static/data/projectCVAT per avere una immagine significativa per progetto (immagine presa dall'ultimo task inserito)

    picture = Image.open(fs[0])
    file_name, file_extension = ntpath.splitext(fs[0])
    pathFirstFile = './app/static/data/projectCVAT/{}{}'.format(taskId, file_extension)
    picture = picture.save(pathFirstFile)

    ############################################################################################################################################################################
    
    shutil.rmtree('temp{}'.format(uuid))

# creo un nuovo progetto inserendo solamente il nome
def create_project(name_project):

    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    dataProject = {
        "name": name_project
    }
    
    createProject = requests.post('{}/projects'.format(url_cvat), data=dataProject, headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(createProject.text)
    projectId = jsonObj['id']
    return projectId

# funzione chiamata nello script dbquery.py per ottenere i dati di uno specifico progetto cvat
def get_project(id_prj_MVE, id_prj_CVAT):

    img = "data/projectCVAT/notasks.png"
    
    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    """
    prj = requests.get('{}/projects/{}'.format(url_cvat, id_prj_CVAT), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    img = "data/projectCVAT/notasks.png"
    nImages = 0
    if (len(jsonObj['tasks']) != 0):
        tasks_id = []
        for t in jsonObj['tasks']:
            tasks_id.append(t)
            prj = requests.get('{}/tasks/{}'.format(url_cvat, t), headers={"Authorization": f'Token {keyLogin}'})
            jsonObjtask = json.loads(prj.text)
            if (jsonObjtask['segments'] == []):
                nImages = nImages + 0
            else:
                nImages = nImages+jsonObjtask['size']
    
    

        files = os.listdir('./app/static/data/projectCVAT')
        for file in files:
            file_name, file_extension = ntpath.splitext(file)
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
    """
    # prendo il progetto CVAT
    prj = requests.get('{}/projects/{}'.format(url_cvat, id_prj_CVAT), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    name = jsonObj['name']

    # prendo i task del progetto CVAT
    tasks = requests.get('{}/projects/{}/tasks'.format(url_cvat, id_prj_CVAT), headers={"Authorization": f'Token {keyLogin}'})
    jsonTasks = json.loads(tasks.text)
    
    # 'results' contiene i task
    if (len(jsonTasks['results']) != 0):
        tasks_id = []
        for t in jsonTasks['results']:
            tasks_id.append(t['id'])

            if (t['segments'] == []):
                size = 0
            else:
                size = t['size']

        files = os.listdir('./app/static/data/projectCVAT')
        for file in files:
            file_name, file_extension = ntpath.splitext(file)
            if (file_name==str(max(tasks_id))):
                img = "data/projectCVAT/{}{}".format(file_name, file_extension)
    else:
        size = 0
        img = "data/projectCVAT/notasks.png"

    project_info = {
        'id_MVE': id_prj_MVE,
        'id_CVAT': id_prj_CVAT,
        'name': name,
        'nTask': len(jsonTasks['results']),
        'nImages': size,
        'img': img
    }

    return(project_info)

# elimino uno specifico progetto cvat
def delete_project(id):

    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    prj = requests.delete('{}/projects/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})

# prendo i task di un progetto cvat specifico
def get_tasks(id):
    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    tasks = requests.get('{}/projects/{}/tasks'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})
    jsonTasks = json.loads(tasks.text)
    task = []
    for jsonTask in jsonTasks['results']:

        if (jsonTask['segments'] == []):
            size = 0
        else:
            size = jsonTask['size']

        date = jsonTask['created_date'][0:10].split("-")

        t = {
            'id': jsonTask['id'],
            'name': jsonTask['name'],
            'date': date[2]+"/"+date[1]+"/"+date[0],
            'size': size
        }
        task.append(t)
    
    return task

# cancello un task specifico
def delete_task(id):
    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    prj = requests.delete('{}/tasks/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})

# prendo gli id di tutti i progetti esistenti su cvat e li metto in una lista
def get_projects_id():
    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    prj = requests.get('{}/projects'.format(url_cvat), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    
    ids = []

    if (jsonObj['results'] != []):
        for result in jsonObj['results']:
            ids.append(result['id'])
    
    return ids

def get_task_dataset(id, folderPath):
    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    while True:
        task = requests.get('{}/tasks/{}/dataset'.format(url_cvat, id), params={"action" : "download", "format":"CVAT for images 1.1", "location":"local"}, headers={"Authorization": f'Token {keyLogin}'})
        if task.status_code == 200:
            break
    
    folderPathzip = "dataset{}zip".format(id)
    
    with open(folderPathzip, 'wb') as fp:
        fp.write(task.content)

    # loading the temp.zip and creating a zip object
    with ZipFile(folderPathzip, 'r') as zObject:
    
        # Extracting all the members of the zip 
        # into a specific location.
        zObject.extractall(path=folderPath)
    
    os.remove(folderPathzip)