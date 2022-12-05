import json
import os
import shutil
import time
from flask import render_template,request, jsonify, redirect, send_file, session, url_for, make_response
from app import app, CVATapi, comparedb, dbquery, truthdb, predictdb
from dotenv import load_dotenv
from queue import Queue
from threading import Thread
from time import sleep

load_dotenv()

## PRIMA DI OGNI RICHIESTA FACCIO QUESTO CONTROLLO ##
#####################################################################################################

@app.before_request
def before_request():

    # controllo che il server cvat sia in run
    #status = CVATapi.check_serverCVAT_connection()
    #if status == 'Server not connect':
        #return make_response(render_template("serverError.html", info="Server non connesso"), 404)
    
    # controllo che i progetti cvat esistenti nel db siano esistenti anche su cvat (in questo modo 
    # eventuali progetti eliminati lato cvat saranno eliminati anche lato db)
    # p_cvat contiene i progetti esistenti su cvat, a prescindere da MVE
    # ps_db contiene i progetti cvat esistenti sul db
    projectsCVAT = CVATapi.get_projects_id()
    projectsCVATdb = dbquery.get_projectsCVAT_id()
    
    for p in projectsCVATdb:
        if p not in projectsCVAT:
            dbquery.delete_projectCVAT(p)
            
## HOME ##
#####################################################################################################

# home page con la vista dei progetti (MVE e CVAT)
@app.route("/")
@app.route("/index")
def index():
  
    # prendo tutti i progetti MVE e CVAT
    projectsMVE = dbquery.get_projectsMVE()
    projectsCVAT =  dbquery.get_projectMVExProjectCVAT() 
    predictions = dbquery.get_predList(id)

    return render_template('index.html', projectsMVE=projectsMVE, projectsCVAT=projectsCVAT, predictions=predictions)

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
@app.route("/edit_projectMVE/<id>")
def edit_projectMVE(id):
    data = dbquery.get_projectMVE(id)
    if (data == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)
    
    predictions = dbquery.get_predList_by_id(id)
    
    return render_template('edit_projectMVE.html', id=id, data=data, predictions=predictions)

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
@app.route("/delete_projectMVE/<id>")
def delete_projectMVE(id):
    
    # controllo che il progetto mve esista
    project = dbquery.get_projectMVE(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    # prendo i progetti cvat associati al progetto mve da eliminare
    prjsCVAT = dbquery.get_projectsCVAT(id)  
    dbquery.delete_projectMVE(id)
    dbquery.delete_MVSxCVAT_MVE(id)
    
    # se esistono elimino ogni progetto cvat
    if (len(prjsCVAT) != 0):
        for pCVAT in prjsCVAT: 
            CVATapi.delete_project(pCVAT[1])

    return redirect(url_for('index'))

## GESTIONE PROGETTI CVAT ##
#####################################################################################################

# VISUALIZZAZIONE di un progetto CVAT
@app.route("/project/<id>")
def project(id):

    # controlliamo che il progetto esista
    project = dbquery.get_projectCVAT(id)

    # otteniamo tutti i progetti per poter cambiare la scelta del progetto corrente dalla pagina project.html
    projectsMVE = dbquery.get_projectsMVE()
    projectsCVAT =  dbquery.get_projectMVExProjectCVAT()

    if (project == []):
        return render_template('project.html', id=id, projectsMVE=projectsMVE, projectsCVAT=projectsCVAT, info="progetto non esistente")
    
    # l'api di cvat ritorna solo 10 task (in questo caso gli ultimi)
    tasks = CVATapi.get_tasks(id)

    return render_template('project.html', id=id, projectsMVE=projectsMVE, projectsCVAT=projectsCVAT, tasks=tasks, info="")


# CREAZIONE di un nuovo progetto CVAT, dato un progetto MVE
@app.route("/new_projectCVAT/<id_prj_MVE>")
def new_projectCVAT(id_prj_MVE):

    # controllo che il progetto mve esista
    project = dbquery.get_projectMVE(id_prj_MVE)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id_prj_MVE)), 404)

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
@app.route("/delete_projectCVAT/<id>")
def delete_projectCVAT(id):

    # controllo che il progetto mve esista
    project = dbquery.get_projectCVAT(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)
    
    tasks = CVATapi.get_tasks_ids(id)
    for task in tasks:
        dbquery.delete_MVSxCVAT_task(task)
        
    dbquery.delete_projectCVAT(id)
    CVATapi.delete_project(id)

    return redirect(url_for('index'))

## TASK MANAGEMENT - THREAD ## 
#####################################################################################################

# La funzione prende dalla coda il primo task inserito poi in un ciclo for scorre tutte le richieste 
# finche non trova qeulla con il task corrispondente. a quel punto prende i dati (uuid, nametask, id) 
# e genera n task cvat con le immagini caricate
def worker(queue):
    while True:
        # get the next task, blocking until one is available.
        task = queue.get()
        # The app is available to the worker, but be wary of
        # using app services without locking.
        ##### WORK TO DO IN BACKGROUND #####
        
        for request in requests:
            if (request['task']==task):
                uuid = request['uuid']
                name_task = request['name_task']
                id = request['id_prjCVAT']
                keyLogin = CVATapi.generate_key_login()

                idMVE = dbquery.get_projectCVAT(id)[0]
                
                directory = 'temp{}'.format(uuid)
                dir = os.listdir(directory)
                current_task = 1

                # Checking if the list is empty or not
                while len(dir) != 0:
                    taskId = CVATapi.create_empty_task(id, name_task, current_task, keyLogin)

                    fs = CVATapi.select_images(uuid, idMVE, taskId)

                    CVATapi.upload_images(uuid, fs, keyLogin, taskId)
                    current_task = current_task + 1
                    dir = os.listdir(directory)

                shutil.rmtree(directory)
        for request in requests.copy():
            if (request['task']==task):
                requests.remove(request)
                
                #duration = app.config.get('WORK_TIME', 3)
                
                #sleep(duration)  # simulate doing work
                print("did task {!r}".format(task))

# Give the worker thread a Queue that's shared with the app, and start
# the worker. The worker will block immediately until a task is added
# to the queue.
work_queue = Queue()
worker_thread = Thread(target=worker, args=(work_queue,), daemon=True)
worker_thread.start()
requests = []
task = 0

## CARICAMENTO IMMAGINI - CREAZIONE DI TASK - ELIMINAZIONE TASK ##
#####################################################################################################

# CARICAMENTO immagini
@app.route('/upload/<id>')
def upload(id):
    # controllo che il progetto sia esistente
    project = dbquery.get_projectCVAT(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    return render_template('upload_img.html', id=id)

@app.route('/get_regex_file', methods=['GET', 'POST'])
def get_regex_file():
    if request.method == "POST":
        data = request.get_json()
    
    session['regex'+data['uuid']] = data['data']

    return "ok"
# Caricamento effettivo delle immagini e creazione di n task a seconda del peso totale delle immagini
# NB. questa rotta viene raggiunta quando viene eseguito il submit del form presente alla pagina upload_img.html;
# ogni volta che viene fatto un submit viene incrementato il numero di task (niente a che fare con cvat, in qeusto caso è
# una variabile globale) e viene creata una istanza this_request con i dati della richiesta corrente con anche il numero del task 
# corrispondente. questa istanza viene aggiunta ad una lista di richieste (requests). viene creato un nuovo thread che chiama 
# la funzione "warker" con parametro una coda (work_queue) di task. Vedi funzione per vedere cosa succede  
@app.route('/uploader/<id>', methods=['POST', 'GET'])
def uploader(id):
    this_name_task = request.form['name-task']
    files = request.files.getlist('fileList')
    this_uuid = request.form.get('uuid')
    regex = session['regex'+this_uuid]
    regex_files = []
    for file in files:
        if file.filename in regex:
            regex_files.append(file)
    session.pop('regex'+this_uuid)

    totalSize = CVATapi.get_files(regex_files, this_uuid)
    global task
    task += 1
    this_request = {
        'task': task,
        'uuid': this_uuid,
        'name_task': this_name_task,
        'id_prjCVAT': id
    }
    global requests
    requests.append(this_request)
    print("add task {!r}".format(task))
    work_queue.put(task)
    return redirect(url_for('project', id=id))

# ELIMINAZIONE di un task
@app.route("/delete_task/<id>")
def delete_task(id):

    prj_id = request.args.get('prj_id')
    CVATapi.delete_task(id)
    dbquery.delete_MVSxCVAT_task(id)

    return redirect(url_for('project', id=prj_id))

## VERITA ## 
#####################################################################################################

# NB l'id che passo come parametro è l'id del progetto MVE scelto

# CARICAMENTO truth
@app.route("/upload_truth/<id>")
def upload_truth(id):
    # controllo che il progetto mve esista
    project = dbquery.get_projectMVE(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    return render_template('upload_truth.html', id=id)

# Caricamento effettivo del file e aggiunta di istanze nelle tabelle Truth e TruthValues
@app.route('/uploader_truth/<id>', methods=['POST', 'GET'])
def uploader_truth(id):
    file_truth = request.files['file-truth']
    resp = truthdb.read_file(file_truth,id)
    session['duplicates'] = resp
    
    return redirect(url_for('upload_truth', id=id))

# SCARICAMENTO verita
@app.route('/download_truth/<id>', methods=['POST', 'GET'])
def download_truth(id):
    truthdb.download_truth(id)
    namefile = truthdb.download_truth(id)
    return send_file("../"+namefile, as_attachment=True)

## PREDIZIONI ## 
#####################################################################################################

# NB l'id che passo come parametro è l'id del progetto MVE scelto

# CARICAMENTO predizione
@app.route("/upload_prediction/<id>")
def upload_prediction(id):
    # controllo che il progetto mve esista
    project = dbquery.get_projectMVE(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    return render_template('upload_prediction.html', id=id)

# Caricamento effettivo del file e aggiunta di istanze nelle tabelle Truth e TruthValues
@app.route('/uploader_prediction/<id>', methods=['POST', 'GET'])
def uploader_prediction(id):
    file_truth = request.files['file-pred']
    
    return predictdb.read_file(file_truth,id)

# ELIMINAZIONE di una predizione
@app.route("/delete_prediction/<id>")
def delete_prediction(id):

    dbquery.delete_prediction(id)
    prj_id = request.args.get('prj_id')

    return redirect(url_for('edit_projectMVE', id=prj_id))

# SCARICAMENTO predizione
@app.route('/download_pred/<id>', methods=['POST', 'GET'])
def download_pred(id):
    if request.method == "POST":
        pred = request.form['select-prediction']
        namefile = predictdb.download_pred(id, pred)
        return send_file("../"+namefile, as_attachment=True)
    return redirect(url_for('index'))

## CONFRONTO PREDIZIONI/VERITA  ##
#####################################################################################################

# pagina principale
@app.route("/compare/<id>")
def compare(id):
    comparisons = comparedb.get_comparisons(id)
    predictions = dbquery.get_predList_by_id(id)
    truth = dbquery.get_truth_mve(id)

    return render_template('compare.html', id=id, predictions=predictions, comparisons=comparisons, truth=truth)

# Visualizza predizione
@app.route("/view_prediction/<id>",  methods=['POST', 'GET'])
def view_prediction(id):
    if request.method == "POST":
        pred = request.form['select-prediction']
        
        comparedb.view_prediction(id, pred)

    return redirect(url_for('compare', id=id))

# Confronto predizioni 
@app.route("/compare_predictions/<id>",  methods=['POST', 'GET'])
def compare_predictions(id):
    if request.method == "POST":
        pred1 = request.form['select-first-prediction']
        pred2 = request.form['select-second-prediction']
        
        comparedb.compare_predictions(id, pred1, pred2)

    return redirect(url_for('compare', id=id))

# Confronto predizione vs verita 
@app.route("/compare_pred_truth/<id>",  methods=['POST', 'GET'])
def compare_pred_truth(id):
    if request.method == "POST":
        pred = request.form['select-prediction']
        
        comparedb.compare_pred_truth(id, pred)

    return redirect(url_for('compare', id=id))

# ELIMINAZIONE di un confronto
@app.route("/delete_compare/<id>")
def delete_compare(id):
    dir_name = request.args.get('dir_name')
    shutil.rmtree('datasets/'+dir_name)
    return redirect(url_for('compare', id=id))

# Visualizza qualcosa di gia esistente
@app.route("/compare_existing/<id>",  methods=['POST', 'GET'])
def compare_existing(id):
    pred1 = request.args.get('pred1')
    tab = request.args.get('pred2')
    if (tab == "/"):
        comparedb.view_prediction(id, pred1)
    elif (tab == "Truth"):
        comparedb.compare_pred_truth(id, pred1)
    else:
        comparedb.compare_predictions(id, pred1, tab)

    return redirect(url_for('compare', id=id))

## GESTIONE ERRORI  ##
#####################################################################################################

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', info="Pagina non trovata"), 404