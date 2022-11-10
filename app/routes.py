import math
import os, json
import shutil
from flask import render_template,request, jsonify, redirect, session, url_for
from app import app, uploadImgs, dbquery
import requests
import io
from PIL import Image
import numpy
import random
import ntpath
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from pathlib import Path
import mysql.connector

load_dotenv()

username = os.getenv('USERNAME_CVAT')
password = os.getenv('PASSWORD_CVAT')
max_size_load_file = os.getenv('MAX_SIZE_LOAD_FILE')
user_db = os.getenv('USER_DB')
name_db = os.getenv('NAME_DB')
project_id = 10
name_task = 'My Task'

params = {
    'user': user_db, 
    'database': name_db
}

@app.route("/index")
def index():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM ProjectsMVE")

    data = mycursor.fetchall()
    print(data)

    return render_template('index.html', data=data)

@app.route("/new_project")
def new_project():
    return render_template('new_project.html')

@app.route("/new_project_data", methods=['POST', 'GET'])
def new_project_data():
    mydb = mysql.connector.connect(**params)
    if request.method == "POST": 
        name_prj = request.form['name-project']
        desc_prj = request.form['desc-project']
        img_prj = request.files['img-project']
        dbquery.new_project(mydb, name_prj,desc_prj, img_prj)
        
        return redirect(url_for('index'))
    return ('',204)

@app.route("/project")
def project():
    return render_template('project.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST', 'GET'])
def uploader():
    files = request.files.getlist('fileList')
    uploadImgs.uploadImages(username, password, name_task, files)
    return ('',204)

"""

def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

@socketio.on('connect')
def test_connect():
    emit('after connect',  {'data':'Lets dance'})

@socketio.on('my event', namespace='/upload')
def prova():
    emit('my response', {'data': 'got it!'}) """

"""

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

@app.route('/home', methods=['POST', 'GET'])
def home():
    pathFolder = 'temp'

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

    getProjects = requests.get('http://localhost:8080/api/v1/projects', headers={"Authorization": f'Token {keyLogin}'})
    jsonObj = json.loads(getProjects.text)
    results = jsonObj['results']
    for result in results:
        print(result['name'] + " " + str(result['id']))

    return render_template('index.html')

@app.route('/test_uploader', methods=['POST', 'GET'])
def test_uploader():
    
    if request.method == "POST":
        pathFolder = 'temp'

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
            "name": name_task + " #1",
            "project_id": project_id,
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

        files = request.files.getlist('fileList')
        fs = []
        
        for file in files:
            headfp, tailfp = ntpath.split(file.filename)
            
            pathFile = "temp/" + tailfp
            file.save(pathFile)
            fs.append(pathFile)
            
        images = {f'client_files[{i}]': open(f, 'rb') for i, f in enumerate(fs)}
        
        uploadImgs = requests.post('http://localhost:8080/api/v1/tasks/{}/data'.format(taskId),data={"image_quality": 100}, files=images, headers={"Authorization": f'Token {keyLogin}'})
        print(uploadImgs.text)
    
        shutil.rmtree('temp')
    return ('',204)
"""
