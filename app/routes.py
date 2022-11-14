import math
import os, json
import shutil
from flask import render_template,request, jsonify, redirect, session, url_for
from app import app, CVATapi, dbquery
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

name_task = 'My Task'

## HOME ##
#####################################################################################################

# home page con la vista dei progetti (MVE e CVAT)
@app.route("/")
@app.route("/index")
def index():
    
    projectsMVE = dbquery.get_projectsMVE()

    projectsCVAT =  dbquery.get_projectMVExProjectCVAT()

    return render_template('index.html', projectsMVE=projectsMVE, projectsCVAT=projectsCVAT)

## GESTIONE PROGETTI MVE ##
#####################################################################################################

# CREAZIONE di un nuovo progetto MVE
@app.route("/new_projectMVE")
def new_projectMVE():
    return render_template('new_projectMVE.html')

# Ricezione dei dati per la creazione di un nuovo progetto MVE
@app.route("/new_projectMVE_data", methods=['POST', 'GET'])
def new_projectMVE_data():

    if request.method == "POST": 
        name_prj = request.form['name-project']
        desc_prj = request.form['desc-project']
        img_prj = request.files['img-project']
        dbquery.new_projectMVE(name_prj,desc_prj, img_prj)
        
        return redirect(url_for('index'))
    return ('',204)

# MODIFICA di un nuovo progetto MVE
@app.route("/edit_projectMVE/<projectMVE>")
def edit_projectMVE(projectMVE):
    data = dbquery.get_projectMVE(projectMVE)
    return render_template('edit_projectMVE.html',data=data)

# Ricezione dei dati per la modifica di un nuovo progetto MVE
@app.route("/edit_projectMVE_data", methods=['POST', 'GET'])
def edit_projectMVE_data():

    if request.method == "POST": 
        id_prj = request.form['id-project']
        name_prj = request.form['name-project']
        desc_prj = request.form['desc-project']
        img_prj = request.files['img-project']
        
        dbquery.edit_projectMVE(id_prj, name_prj,desc_prj, img_prj)
        
        return redirect(url_for('index'))
    return ('',204)

# ELIMINAZIONE di un progetto MVE
@app.route("/delete_projectMVE/<projectMVE>")
def delete_projectMVE(projectMVE):
    prjsCVAT = dbquery.get_projectsCVAT(projectMVE)  # progetti cvat associati al progetto mve da eliminare
    dbquery.delete_projectMVE(projectMVE)
    
    if (len(prjsCVAT) != 0):
        for pCVAT in prjsCVAT: 
            CVATapi.delete_project(pCVAT[1])

    return redirect(url_for('index'))

## GESTIONE PROGETTI CVAT ##
#####################################################################################################

# VISUALIZZAZIONE di un progetto CVAT
@app.route("/project/<id>")
def project(id):

    projectsMVE = dbquery.get_projectsMVE()
    # otteniamo tutti i progetti per poter cambiare la scelta del progetto corrente dalla pagina project.html
    projectsCVAT =  dbquery.get_projectMVExProjectCVAT()

    return render_template('project.html', id=id, projectsMVE=projectsMVE, projectsCVAT=projectsCVAT)


# CREAZIONE di un nuovo progetto CVAT, dato un progetto MVE
@app.route("/new_projectCVAT/<id_prj_MVE>")
def new_projectCVAT(id_prj_MVE):
    name_prj_MVE = request.args.get('name_prj_MVE')
    
    return render_template('new_projectCVAT.html', id_prj_MVE=id_prj_MVE, name_prj_MVE=name_prj_MVE)

# Ricezione dei dati per la creazione di un nuovo progetto CVAT
@app.route("/new_projectCVAT_data", methods=['POST', 'GET'])
def new_projectCVAT_data():
    if request.method == "POST": 
        name_prj = request.form['name-project']
        id_prj_MVE = request.form['id-prj-MVE']
        
        id_prj_CVAT = CVATapi.create_project(name_prj)

        dbquery.new_projectCVAT(id_prj_MVE, id_prj_CVAT)
        
        return redirect(url_for('index'))
    return ('',204)

# ELIMINAZIONE di un progetto CVAT
@app.route("/delete_projectCVAT/<projectCVAT>")
def delete_projectCVAT(projectCVAT):

    dbquery.delete_projectCVAT(projectCVAT)
    CVATapi.delete_project(projectCVAT)

    return redirect(url_for('index'))

# Caricamento immaginix
@app.route('/upload/<id>')
def upload(id):
    return render_template('upload.html', id=id)

# Caricamento effettivo delle immagini e creazione di n task a seconda del peso totale delle immagini
@app.route('/uploader/<id>', methods=['POST', 'GET'])
def uploader(id):
    files = request.files.getlist('fileList')
    CVATapi.uploadImages(id, name_task, files)
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
