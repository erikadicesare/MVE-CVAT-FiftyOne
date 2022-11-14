from pathlib import Path
import mysql.connector
from app import CVATapi
import ntpath, os
from dotenv import load_dotenv

load_dotenv()

user_db = os.getenv('USER_DB')
name_db = os.getenv('NAME_DB')
pw_db = os.getenv('PW_DB')

params = {
    'user': user_db, 
    'database': name_db,
    'password': pw_db
}

def new_projectMVE(name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)

    headfp, tailfp = ntpath.split(img_prj.filename)
    url_img_prj = './app/static/data/project-icon/' + tailfp
    img_prj.save(url_img_prj)
    relative_path = "data/project-icon/" + tailfp
    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectsMVE (NomeProgetto, Descrizione, ImmagineDescrittiva) VALUES (%s, %s, %s)"
    val = (name_prj, desc_prj, relative_path)
    mycursor.execute(sql, val)

    mydb.commit()

def edit_projectMVE(id_prj, name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)
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

def delete_projectMVE(id_prj):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM ProjectsMVE WHERE IdProjectMVE=%s", (id_prj,))

    mydb.commit()
    #dataform.create_file(task)

def new_projectCVAT(id_prj_MVE, id_prj_CVAT):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectMVExProjectCVAT (IdProjectMVE, IdProjectCVAT) VALUES (%s, %s)"
    val = (id_prj_MVE, id_prj_CVAT)
    mycursor.execute(sql, val)

    mydb.commit()

def get_projectsMVE():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE")
    projectsMVE = mycursor.fetchall()

    return projectsMVE

def get_projectMVE(id):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE WHERE IdProjectMVE=%s", (id,))
    projectsMVE = mycursor.fetchall()

    return projectsMVE[0]

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