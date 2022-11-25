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

def generate_key_login():

    login = requests.post('{}/auth/login'.format(url_cvat), json= credentials)
    jsonObj = json.loads(login.text)
    keyLogin = jsonObj['key']

    return keyLogin

def get_files(files, uuid):

    pathFolder = 'temp{}'.format(uuid)

    # controllo se la cartella esiste 
    isExist = os.path.exists(pathFolder)
    
    # creo la cartella se non esiste
    if not isExist:
        os.makedirs(pathFolder)

    totalSize = 0
    for file in files:
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        file.save(pathFile)
        totalSize = totalSize + Path(pathFile).stat().st_size

    return totalSize

def create_empty_task(id, name_task, i, keyLogin):

    dataTask = {
        "name": name_task + " #"+str(i),
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

    return taskId

def select_images(uuid, idMVE, taskId):
    directory = 'temp{}'.format(uuid)
    fs = []
    size = 0 

    for filename in os.listdir(directory):
        
        pathFile = 'temp{}/'.format(uuid) + filename
        size_file = Path(pathFile).stat().st_size
        #size = size + size_file
        if (size+size_file<int(max_size_load_file)):
            size = size + size_file
            fs.append(pathFile)
            check = dbquery.get_MVSxCVAT(filename, idMVE)
            if check == 0: 
                dbquery.insert_MVSxCVAT_row(filename, idMVE, taskId)
        else:
            return fs

    return fs

def upload_images(uuid, fs, keyLogin, taskId):
    directory = 'temp{}'.format(uuid)

    images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
    uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
    print(uploadImgs.text)
    save_image_cover(fs[0], taskId)
    for f in fs:
        os.remove(f)

def save_image_cover(fs, taskId):
    # Salvo il primo file dentro static/data/projectCVAT per avere una immagine significativa per progetto (immagine presa dall'ultimo task inserito)
    picture = Image.open(fs)
    file_name, file_extension = ntpath.splitext(fs)
    pathFirstFile = './app/static/data/projectCVAT/{}{}'.format(taskId, file_extension)
    picture = picture.save(pathFirstFile)

"""
def uploadImages(id, name_task, files, uuid):

    keyLogin = generate_key_login()
        
    totalSize = get_files(files, uuid)
        
    taskId = create_empty_task(id, name_task, 1, keyLogin)

    idMVE = dbquery.get_projectCVAT(id)[0]
    
    fs = []
    size = 0 
    countTask = 1

    fs = select_images(uuid, idMVE, taskId)

    upload_images(uuid, fs, keyLogin, taskId)

    
    for file in files:
        headfp, tailfp = ntpath.split(file.filename)
        
        pathFile = 'temp{}/'.format(uuid) + tailfp
        
        size = size + Path(pathFile).stat().st_size
        if (size<int(max_size_load_file)):
            fs.append(pathFile)
            check = dbquery.get_MVSxCVAT(tailfp, idMVE)
            if check == 0: 
                dbquery.insert_MVSxCVAT_row(tailfp, idMVE, taskId)
        else:
            images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
            uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
            
            fs = [pathFile]
            size = Path(pathFile).stat().st_size
            if (size!=0):
                countTask = countTask + 1
                taskId = create_empty_task(id, name_task, str(countTask), keyLogin)
                # controllo se esiste gia una immagine con lo stesso nome in cvat
                check = dbquery.get_MVSxCVAT(tailfp, idMVE)
                if check == 0: 
                    dbquery.insert_MVSxCVAT_row(tailfp, idMVE, taskId)
    if (size>0): 
        images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
        uploadImgs = requests.post('{}/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
    
    ############################################################################################################################################################################
    
    # Salvo il primo file dentro static/data/projectCVAT per avere una immagine significativa per progetto (immagine presa dall'ultimo task inserito)

    picture = Image.open(fs[0])
    file_name, file_extension = ntpath.splitext(fs[0])
    pathFirstFile = './app/static/data/projectCVAT/{}{}'.format(taskId, file_extension)
    picture = picture.save(pathFirstFile)

    ############################################################################################################################################################################
    
    #shutil.rmtree('temp{}'.format(uuid))
    """
# creo un nuovo progetto inserendo solamente il nome
def create_project(name_project):

    keyLogin = generate_key_login()

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
    
    keyLogin = generate_key_login()

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

    keyLogin = generate_key_login()

    prj = requests.delete('{}/projects/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})

# prendo i task di un progetto cvat specifico
def get_tasks(id):

    keyLogin = generate_key_login()

    tasks = requests.get('{}/projects/{}/tasks'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})
    jsonTasks = json.loads(tasks.text)
    task = []
    for jsonTask in jsonTasks['results']:

        if (jsonTask['segments'] == []):
            size = 0
        else:
            size = jsonTask['size']
        
        date = jsonTask['created_date'][0:10].split("-")
        time = jsonTask['created_date'][11:19].split(":")
        
        t = {
            'id': jsonTask['id'],
            'name': jsonTask['name'],
            'date': date[2]+"/"+date[1]+"/"+date[0],
            'time': time[0]+":"+time[1],
            'size': size
        }
        task.append(t)
    
    return task

# prendo gli id dei task di un progetto cvat specifico
def get_tasks_ids(id):
    keyLogin = generate_key_login()

    tasks = requests.get('{}/projects/{}/tasks'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})
    jsonTasks = json.loads(tasks.text)
    ids = []
    for jsonTask in jsonTasks['results']:
        ids.append(jsonTask['id'])
    
    return ids

# cancello un task specifico
def delete_task(id):
    keyLogin = generate_key_login()

    prj = requests.delete('{}/tasks/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})

# prendo gli id di tutti i progetti esistenti su cvat e li metto in una lista
def get_projects_id():
    keyLogin = generate_key_login()

    prj = requests.get('{}/projects'.format(url_cvat), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    
    ids = []

    if (jsonObj['results'] != []):
        for result in jsonObj['results']:
            ids.append(result['id'])
    
    return ids

def get_task_dataset(id, folderPath):
    keyLogin = generate_key_login()

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