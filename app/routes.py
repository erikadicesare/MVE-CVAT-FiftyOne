from flask import render_template,request, jsonify, redirect, url_for, make_response
from app import app, CVATapi, dbquery
from dotenv import load_dotenv

load_dotenv()

## PRIMA DI OGNI RICHIESTA FACCIO QUESTO CONTROLLO ##
#####################################################################################################

@app.before_request
def before_request():
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
@app.route("/edit_projectMVE/<id>")
def edit_projectMVE(id):
    data = dbquery.get_projectMVE(id)
    if (data == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)
    
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
@app.route("/delete_projectMVE/<id>")
def delete_projectMVE(id):
    
    # controllo che il progetto mve esista
    project = dbquery.get_projectMVE(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    # prendo i progetti cvat associati al progetto mve da eliminare
    prjsCVAT = dbquery.get_projectsCVAT(id)  
    dbquery.delete_projectMVE(id)
    
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
    
    dbquery.delete_projectCVAT(id)
    CVATapi.delete_project(id)

    return redirect(url_for('index'))

## CARICAMENTO IMMAGINI - CREAZIONE DI TASK - ELIMINAZIONE TASK ##
#####################################################################################################

# Caricamento immagini
@app.route('/upload/<id>')
def upload(id):
    
    # controllo che il progetto sia esistente
    project = dbquery.get_projectCVAT(id)
    if (project == []):
        return make_response(render_template("404.html", info="Il progetto {} non esiste".format(id)), 404)

    return render_template('upload.html', id=id)

# Caricamento effettivo delle immagini e creazione di n task a seconda del peso totale delle immagini
@app.route('/uploader/<id>', methods=['POST', 'GET'])
def uploader(id):
    name_task = request.form['name-task']
    files = request.files.getlist('fileList')
    CVATapi.uploadImages(id, name_task, files)
    return redirect(url_for('project', id=id))

# ELIMINAZIONE di un task
@app.route("/delete_task/<id>")
def delete_task(id):

    prj_id = request.args.get('prj_id')
    CVATapi.delete_task(id)

    return redirect(url_for('project', id=prj_id))

## GESTIONE ERRORI  ##
#####################################################################################################

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', info="Pagina non trovata"), 404