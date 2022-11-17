from pathlib import Path
import mysql.connector
from app import CVATapi
import ntpath, os
from dotenv import load_dotenv

load_dotenv()

user_db = os.getenv('USER_DB')
name_db = os.getenv('NAME_DB')
#pw_db = os.getenv('PW_DB')

params = {
    'user': user_db, 
    'database': name_db,
    #'password': pw_db
}

# creazione nuovo progetto MVE 
def new_projectMVE(name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)

    # salvo l'immagine inserita dall'utente nella cartella /static/data/project-icon/ 
    headfp, tailfp = ntpath.split(img_prj.filename)
    url_img_prj = './app/static/data/project-icon/' + tailfp
    img_prj.save(url_img_prj)
    relative_path = "data/project-icon/" + tailfp

    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectsMVE (NomeProgetto, Descrizione, ImmagineDescrittiva) VALUES (%s, %s, %s)"
    val = (name_prj, desc_prj, relative_path)
    mycursor.execute(sql, val)

    mydb.commit()

# modifica di un progetto MVE
def edit_projectMVE(id_prj, name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)

    # se l'utente decide di non modificare l'immagine, vado aprendere quella esistente, altrimenti uso quella appena inserita
    if img_prj.filename == '':
        mycursor = mydb.cursor()
        mycursor.execute("SELECT ImmagineDescrittiva FROM ProjectsMVE WHERE IdProjectMVE=%s", (id_prj,))
        projectsMVE = mycursor.fetchone()
        relative_path = projectsMVE[0]
    else:
        headfp, tailfp = ntpath.split(img_prj.filename)
        url_img_prj = './app/static/data/project-icon/' + tailfp
        img_prj.save(url_img_prj)
        relative_path = "data/project-icon/" + tailfp

    mycursor = mydb.cursor()

    mycursor.execute ("""
    UPDATE ProjectsMVE
    SET NomeProgetto=%s, Descrizione=%s, ImmagineDescrittiva=%s
    WHERE IdProjectMVE=%s
    """, (name_prj, desc_prj, relative_path, id_prj))

    mydb.commit()

# eliminazione di un progetto MVE (in automatico elimina i progetti CVAT associati perché c'è l'opzione on cascade nel db)
def delete_projectMVE(id_prj):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM ProjectsMVE WHERE IdProjectMVE=%s", (id_prj,))

    mydb.commit()

# eliminazione di un progetto CVAT 
def delete_projectCVAT(id_prj):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM ProjectMVExProjectCVAT WHERE IdProjectCVAT=%s", (id_prj,))

    mydb.commit()

# creazione di un nuovo progetto CVAT nel db (coppia di chiavi idMVExidCVAT)
def new_projectCVAT(id_prj_MVE, id_prj_CVAT):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectMVExProjectCVAT (IdProjectMVE, IdProjectCVAT) VALUES (%s, %s)"
    val = (id_prj_MVE, id_prj_CVAT)
    mycursor.execute(sql, val)

    mydb.commit()

# ottengo tutti i progetti MVE
def get_projectsMVE():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE")
    projectsMVE = mycursor.fetchall()

    return projectsMVE

# ottengo un progetto mve specifico
def get_projectMVE(id):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE WHERE IdProjectMVE=%s", (id,))
    projectsMVE = mycursor.fetchall()
    if (projectsMVE==[]):
        return projectsMVE
    else:
        return projectsMVE[0]

# ottengo tutti i progetti CVAT associati a un progetto MVE specifico
def get_projectsCVAT(id):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT WHERE IdProjectMVE=%s", (id,))
    projectsCVAT = mycursor.fetchall()

    return projectsCVAT

# ottengo un progetto CVAT specifico 
def get_projectCVAT(id):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT WHERE IdProjectCVAT=%s", (id,))
    projectCVAT = mycursor.fetchall()
    if (projectCVAT==[]):
        return projectCVAT
    else:
        return projectCVAT[0]

# creo array di oggetti, un oggetto per ogni progetto CVAT.
# per ogni progetto CVAT faccio una chiamata alla funzione get_project che mi restituisce le informazioni 
# un oggetto con le informazioni del progetto CVAT (nome, numero di task, numero di immagini)
def get_projectMVExProjectCVAT():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT ")
    projectsCVAT = mycursor.fetchall()
    
    psCVAT = []
    for projectCVAT in projectsCVAT:
        id_prj_MVE = projectCVAT[0]
        id_prj_CVAT = projectCVAT[1]
        project = CVATapi.get_project(id_prj_MVE, id_prj_CVAT)

        psCVAT.append(project)

    return psCVAT

# prendo gli id dei progetti cvat presenti del db
def get_projectsCVAT_id():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdProjectCVAT FROM ProjectMVExProjectCVAT ")
    projectsCVAT = mycursor.fetchall()

    ids = []
    if (len(projectsCVAT) != 0):

        for pCVAT in projectsCVAT:
            ids.append(pCVAT[0])

    return ids

# creo una istanza nella tabella Truth
def insert_truth(idMVE, name):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO Truth (IdProjectMVE, Name) VALUES (%s, %s)"
    val = (idMVE, name)
    mycursor.execute(sql, val)

    mydb.commit()
    ItemID = mycursor.lastrowid
    return ItemID

# creo una istanza nella tabella TruthValues
def insert_truth_values(idTruth, propName, valReal, valStr):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO TruthValues (IdTruth, PropName, ValueReal, ValueString) VALUES (%s, %s, %s, %s)"
    val = (idTruth, propName, valReal, valStr)
    mycursor.execute(sql, val)

    mydb.commit()