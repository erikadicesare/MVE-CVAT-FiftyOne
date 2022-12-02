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
from time import sleep
from cvat_sdk.api_client import Configuration, ApiClient, models, apis, exceptions

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

    tasks = requests.get('{}/projects/{}/tasks'.format(url_cvat, id), params={"page_size" :1000},headers={"Authorization": f'Token {keyLogin}'})
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

"""
def prova():
    configuration = Configuration(
        host="http://192.168.1.92:8080",
        username=username,
        password=password,
    )

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Parameters can be passed as a plain dict with JSON-serialized data
        # or as model objects (from cvat_sdk.api_client.models), including
        # mixed variants.
        #
        # In case of dicts, keys must be the same as members of models.I<ModelName>
        # interfaces and values must be convertible to the corresponding member
        # value types (e.g. a date or string enum value can be parsed from a string).
        #
        # In case of model objects, data must be of the corresponding
        # models.<ModelName> types.
        #
        # Let's use a dict here. It should look like models.ITaskWriteRequest
        task_spec = {
            'name': 'example task',
            "labels": [{
                "name": "car",
                "color": "#ff00ff",
                "attributes": [
                    {
                        "name": "a",
                        "mutable": True,
                        "input_type": "number",
                        "default_value": "5",
                        "values": ["4", "5", "6"]
                    }
                ]
            }],
        }

        try:
            # Apis can be accessed as ApiClient class members
            # We use different models for input and output data. For input data,
            # models are typically called like "*Request". Output data models have
            # no suffix.
            (task, response) = api_client.tasks_api.create(task_spec)
        except exceptions.ApiException as e:
            # We can catch the basic exception type, or a derived type
            print("Exception when trying to create a task: %s\n" % e)

        fs = []

        for filename in os.listdir('/home/musausr/images/cvat3'):
           
            fs.append('/home/musausr/images/cvat3/'+filename)
   
        images = [open(f, 'rb') for i, f in enumerate(fs)]
        # Here we will use models instead of a dict
        task_data = models.DataRequest(
            image_quality=75,
            client_files=images,
        )
        

        # If we pass binary file objects, we need to specify content type.
        # For this endpoint, we don't have response data
        (_, response) = api_client.tasks_api.create_data(task.id,
            data_request=task_data,
            _content_type="multipart/form-data",

            # we can choose to check the response status manually
            # and disable the response data parsing
            _check_status=False, _parse_response=False
        )
        assert response.status == 202, response.msg

        # Wait till task data is processed
        for _ in range(100):
            (status, _) = api_client.tasks_api.retrieve_status(task.id)
            if status.state.value in ['Finished', 'Failed']:
                break
            sleep(0.1)
        assert status.state.value == 'Finished', status.message

        # Update the task object and check the task size
        (task, _) = api_client.tasks_api.retrieve(task.id)
        assert task.size == 4
"""