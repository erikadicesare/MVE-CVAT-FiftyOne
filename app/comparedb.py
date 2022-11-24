import os
import shutil
from app import dbquery, CVATapi, foIntegration
import xml.etree.ElementTree as ET    
import time

def view_prediction(id, pred):
    images = dbquery.get_MVSxCVAT(id)
    idsMVSpred = dbquery.get_prediction_ids(pred)
    tasks = []
    idsCVAT = []
    for idMVSpred in idsMVSpred:
            for img in images:
                if idMVSpred in img[0]:
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    imagesPath = "datasets/{}/dataset/images/".format(pred)
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    
    # creo la cartella se non esiste e creo il dataset
    if not isExist:
        os.makedirs(imagesPath)

        annotationPath = "datasets/{}/dataset/annotation.xml".format(pred)

        # Preparo il nuovo file xml con le annotazioni delle sole immagini che mi interessano
        rootDest = ET.Element("annotations")
        
        m1 = ET.Element("version")
        m1.text = "1.1"
        rootDest.append(m1)
        
        index = 0
        hasAnnotations = False

        for task in tasks:
            taskPath = "datasets/{}/task{}".format(pred, task)
            CVATapi.get_task_dataset(task, taskPath)
            
            for idCVAT in idsCVAT:
                if os.path.exists(taskPath+"/images/"+idCVAT):
                    
                    shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)
            
            annPath = taskPath+"/annotations.xml"

            tree = ET.parse(annPath)

            rootSource = tree.getroot()

            for child in rootSource:
                if child.tag == "image":
                    if (child.attrib['name'] in idsCVAT):
                        
                        m2 = ET.Element("image", id=str(index), name=child.attrib['name'], width=child.attrib['width'], height=child.attrib['height'])
                        m2.text = " "
                        rootDest.append(m2)

                        # QUESTO IN TEORIA SERVE SOLO SE SI CONFRONTA CON LA VERITA, PERCHE LE ANNOTAZIONI PRESENTI SU CVAT SONO QUELLE RELATIVE ALLA VERITA
                        # MOMENTANEAMENTE LASCIO COSI
                        # IN UN SECONDO MOMENTO VERRANNO PRESI I DATI DI DUE FILE XML DIVERSI DA QUELLI SCARICATI DA CVAT , OPPURE VERRANNO PRESI DALLE TABELLE 
                        # DI PREDICTION E QUINDI VERRA PRIMA CREATO UN DB FIFTYONE SENZA ANNOTAZIONI E POI VERRANNO AGGIUNTE IN  UN SECONDO MOMENTO COME LE ALTRE
                        # PROPRIETA
                        if len(child) != 0:
                            hasAnnotations = True
                            for c in child:
                                b1 = ET.SubElement(m2, c.tag)
                                b1.text = " "
                                for attr in c.attrib:
                                    b1.set(attr,c.attrib[attr])
                            
                        index = index + 1

            #shutil.rmtree(taskPath)

        tree = ET.ElementTree(rootDest)
        
        with open (annotationPath, "wb") as files :
            tree.write(files)

    epoch = time.time()

    foIntegration.create_fo_dataset(str(epoch), "datasets/{}/dataset/".format(pred), pred, "/", hasAnnotations)


def compare_predictions(id, pred1, pred2):
    
    images = dbquery.get_MVSxCVAT(id)
    idsMVSpred1 = dbquery.get_prediction_ids(pred1)
    idsMVSpred2 = dbquery.get_prediction_ids(pred2)
    tasks = []
    idsCVAT = []
    for idMVSpred1 in idsMVSpred1:
        if idMVSpred1 in idsMVSpred2:
            for img in images:
                if idMVSpred1 in img[0]:
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    imagesPath = "datasets/{}x{}/dataset/images/".format(pred1,pred2)
    imagesPathReverse = "datasets/{}x{}/dataset/images/".format(pred2,pred1)
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    isExistReverse = os.path.exists(imagesPathReverse)
    
    # creo la cartella se non esiste e creo il dataset
    if not isExist and not isExistReverse:
        os.makedirs(imagesPath)

        annotationPath = "datasets/{}x{}/dataset/annotation.xml".format(pred1,pred2)

        # Preparo il nuovo file xml con le annotazioni delle sole immagini che mi interessano
        rootDest = ET.Element("annotations")
        
        m1 = ET.Element("version")
        m1.text = "1.1"
        rootDest.append(m1)
        
        index = 0
        
        for task in tasks:
            taskPath = "datasets/{}x{}/task{}".format(pred1,pred2, task)
            CVATapi.get_task_dataset(task, taskPath)
            
            for idCVAT in idsCVAT:
                if os.path.exists(taskPath+"/images/"+idCVAT):
                    
                    shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)
            
            annPath = taskPath+"/annotations.xml"

            tree = ET.parse(annPath)

            rootSource = tree.getroot()

            for child in rootSource:
                if child.tag == "image":
                    if (child.attrib['name'] in idsCVAT):
                        
                        m2 = ET.Element("image", id=str(index), name=child.attrib['name'], width=child.attrib['width'], height=child.attrib['height'])
                        m2.text = " "
                        rootDest.append(m2)

                        # QUESTO IN TEORIA SERVE SOLO SE SI CONFRONTA CON LA VERITA, PERCHE LE ANNOTAZIONI PRESENTI SU CVAT SONO QUELLE RELATIVE ALLA VERITA
                        # MOMENTANEAMENTE LASCIO COSI
                        # IN UN SECONDO MOMENTO VERRANNO PRESI I DATI DI DUE FILE XML DIVERSI DA QUELLI SCARICATI DA CVAT , OPPURE VERRANNO PRESI DALLE TABELLE 
                        # DI PREDICTION E QUINDI VERRA PRIMA CREATO UN DB FIFTYONE SENZA ANNOTAZIONI E POI VERRANNO AGGIUNTE IN  UN SECONDO MOMENTO COME LE ALTRE
                        # PROPRIETA
                        for c in child:
                            b1 = ET.SubElement(m2, c.tag)
                            b1.text = " "
                            for attr in c.attrib:
                                b1.set(attr,c.attrib[attr])
                            
                        index = index + 1

            shutil.rmtree(taskPath)

        tree = ET.ElementTree(rootDest)
        
        with open (annotationPath, "wb") as files :
            tree.write(files)

        epoch = time.time()

        foIntegration.create_fo_dataset(str(epoch), "datasets/{}x{}/dataset/".format(pred1,pred2), pred1, pred2)

    else:
        # se la cartella esiste vuol dire che ho gia i dati per eseguire il confronto

        epoch = time.time()

        if not isExist:
            foIntegration.create_fo_dataset(str(epoch), "datasets/{}x{}/dataset/".format(pred2,pred1), pred1, pred2)
        elif not isExistReverse:
            foIntegration.create_fo_dataset(str(epoch), "datasets/{}x{}/dataset/".format(pred1,pred2), pred1, pred2)

def compare_pred_truth(id, pred):
    print("ok")
