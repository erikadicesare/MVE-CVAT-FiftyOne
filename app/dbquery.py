from pathlib import Path
import mysql.connector
from app import CVATapi

import ntpath

def new_projectMVE(mydb,name_prj, desc_prj, img_prj):
    headfp, tailfp = ntpath.split(img_prj.filename)
    url_img_prj = './app/static/data/project-icon/' + tailfp
    img_prj.save(url_img_prj)
    relative_path = "data/project-icon/" + tailfp
    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectsMVE (NomeProgetto, Descrizione, ImmagineDescrittiva) VALUES (%s, %s, %s)"
    val = (name_prj, desc_prj, relative_path)
    mycursor.execute(sql, val)

    mydb.commit()
    #dataform.create_file(task)

def new_projectCVAT(mydb,id_prj_MVE, id_prj_CVAT):
    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectMVExProjectCVAT (IdProjectMVE, IdProjectCVAT) VALUES (%s, %s)"
    val = (id_prj_MVE, id_prj_CVAT)
    mycursor.execute(sql, val)

    mydb.commit()

def get_projectsMVE(mydb):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE")
    projectsMVE = mycursor.fetchall()

    return projectsMVE

def get_projectMVExProjectCVAT(mydb):
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