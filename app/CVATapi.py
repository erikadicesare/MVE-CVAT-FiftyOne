from zipfile import ZipFile
import requests
import os, json
from pathlib import Path
import ntpath
from PIL import Image  
from app import dbquery
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('USERNAME_CVAT')
password = os.getenv('PASSWORD_CVAT')
url_cvat = os.getenv('URL_CVAT')

max_num_of_task = 1000
max_size_load_file = os.getenv('MAX_SIZE_LOAD_FILE')

credentials = {
    "username": username,
    "email": "",
    "password": password
}

"""
def check_serverCVAT_connection():
    try:
        login = requests.post('{}/auth/login'.format(url_cvat), json= credentials, timeout=10)
        jsonObj = json.loads(login.text)
        keyLogin = jsonObj['key']
        return keyLogin
    except:
        return 'Server not connect'
"""

def generate_key_login():

    login = requests.post('{}/api/auth/login'.format(url_cvat), json= credentials)
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

    createEmptyTask = requests.post('{}/api/tasks'.format(url_cvat), data=dataTask, headers={"Authorization": f'Token {keyLogin}'})
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
    uploadImgs = requests.post('{}/api/tasks/{}/data'.format(url_cvat,taskId), data={'image_quality':100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
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


# creo un nuovo progetto inserendo solamente il nome
def create_project(name_project):

    keyLogin = generate_key_login()

    dataProject = {
        "name": name_project
    }
    
    createProject = requests.post('{}/api/projects'.format(url_cvat), data=dataProject, headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(createProject.text)
    projectId = jsonObj['id']
    return projectId

# funzione chiamata nello script dbquery.py per ottenere i dati di uno specifico progetto cvat
def get_project(id_prj_MVE, id_prj_CVAT):

    img = "data/projectCVAT/notasks.png"
    
    keyLogin = generate_key_login()

    # prendo il progetto CVAT
    prj = requests.get('{}/api/projects/{}'.format(url_cvat, id_prj_CVAT), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    name = jsonObj['name']

    # prendo i task del progetto CVAT
    tasks = requests.get('{}/api/projects/{}/tasks'.format(url_cvat, id_prj_CVAT),params={"page_size" : max_num_of_task}, headers={"Authorization": f'Token {keyLogin}'})
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

    prj = requests.delete('{}/api/projects/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})

# prendo i task di un progetto cvat specifico
def get_tasks(id):

    keyLogin = generate_key_login()

    tasks = requests.get('{}/api/projects/{}/tasks'.format(url_cvat, id), params={"page_size" : max_num_of_task},headers={"Authorization": f'Token {keyLogin}'})
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

    tasks = requests.get('{}/api/projects/{}/tasks'.format(url_cvat, id), params={"page_size" : max_num_of_task}, headers={"Authorization": f'Token {keyLogin}'})
    jsonTasks = json.loads(tasks.text)
    ids = []
    for jsonTask in jsonTasks['results']:
        ids.append(jsonTask['id'])
    
    return ids

# cancello un task specifico
def delete_task(id):
    keyLogin = generate_key_login()
    
    prj = requests.delete('{}/api/tasks/{}'.format(url_cvat, id), headers={"Authorization": f'Token {keyLogin}'})
    
    # Se esiste elimino l'immagine salvata in "static/data/projectCVAT" durante la creazione del task 
    files = os.listdir('./app/static/data/projectCVAT')
    for file in files:
        file_name, file_extension = ntpath.splitext(file)
        if (file_name==id):
            os.remove("app/static/data/projectCVAT/{}{}".format(file_name, file_extension))

# prendo gli id di tutti i progetti esistenti su cvat e li metto in una lista
def get_projects_id():
    keyLogin = generate_key_login()

    prj = requests.get('{}/api/projects'.format(url_cvat), headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(prj.text)
    
    ids = []

    if (jsonObj['results'] != []):
        for result in jsonObj['results']:
            ids.append(result['id'])
    
    return ids

def get_task_dataset(id, folderPath):
    keyLogin = generate_key_login()

    while True:
        task = requests.get('{}/api/tasks/{}/dataset'.format(url_cvat, id), params={"action" : "download", "format":"CVAT for images 1.1", "location":"local"}, headers={"Authorization": f'Token {keyLogin}'})
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