import os
import shutil
from app import dbquery, CVATapi, foIntegration
import xml.etree.ElementTree as ET    
import time

def view_prediction(id, pred):
    # prendo i nomi delle immagini che ho caricato su cvat
    images = dbquery.get_MVSxCVAT_byMVE(id)

    # prendo gli idMVS di una determinata predizione
    idsMVSpred = dbquery.get_prediction_ids(pred)
    tasks = []
    idsCVAT = []

    # mi salvo i task presi in considerazione nella predizione e i nomi delle immagini interessate
    for idMVSpred in idsMVSpred:
            for img in images:
                if idMVSpred in img[0]:
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    path = "datasets/{}".format(pred)
    revPath = "datasets/{}".format(pred)
   
    get_data(path,revPath,tasks,idsCVAT,pred,"/")

def compare_predictions(id, pred1, pred2):
    
    # prendo le immagini che ho caricato su cvat
    # prendo gli idMVS delle due prediction
    images = dbquery.get_MVSxCVAT_byMVE(id)
    idsMVSpred1 = dbquery.get_prediction_ids(pred1)
    idsMVSpred2 = dbquery.get_prediction_ids(pred2)
    tasks = []
    idsCVAT = []
    # mi salvo i task presenti in entrambe le prediction e gli idsCVAT delle immagini condivise da entrambe le prediction 
    for idMVSpred1 in idsMVSpred1:
        if idMVSpred1 in idsMVSpred2:
            for img in images:
                if idMVSpred1 in img[0]:
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    path = "datasets/{}x{}".format(pred1,pred2)
    revPath = "datasets/{}x{}".format(pred2,pred1)
    
    get_data(path, revPath, tasks, idsCVAT, pred1, pred2)

def get_data(path, revPath, tasks, idsCVAT, pred, predOrTruth):

    # cartella in cui ci andranno le immagini interessate
    imagesPath = path+"/dataset/images/"
    imagesPathReverse = revPath+"/dataset/images/"
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    isExistReverse = os.path.exists(imagesPathReverse)
    
    # creo la cartella se non esiste e creo il dataset
    if not isExist and not isExistReverse:
        os.makedirs(imagesPath)

        annotationPath = path+"/dataset/annotation.xml"
        
        # file aggiuntivo usato per scriverci se un dataset ha annotazioni o meno (in caso di confronto gia esistente si va a pescare questa informazine)
        info = open(path+"/dataset/info.txt", "w")

        # Preparo il nuovo file xml con le annotazioni delle sole immagini che mi interessano
        rootDest = ET.Element("annotations")
        
        m1 = ET.Element("version")
        m1.text = "1.1"
        rootDest.append(m1)
        
        index = 0
        hasAnnotations = 'False'

        # per ogni task scarico in locale il dataset cvat corrispondente (immagini + file con annotazioni)
        for task in tasks:
            taskPath = path+"/task{}".format(task)
            CVATapi.get_task_dataset(task, taskPath)
            
            # copio in un altra cartella le immagini che ci interessano 
            for idCVAT in idsCVAT:
                if os.path.exists(taskPath+"/images/"+idCVAT):
                    
                    shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)
            
            # prendo il file delle annotazioni scaricato da cvat e lo esamino
            annPath = taskPath+"/annotations.xml"

            tree = ET.parse(annPath)

            rootSource = tree.getroot()

            # controlo i tag 'image' e se l'attributo 'name' e' tra gli idsCVAT salvati prima allora aggiungo un elemento al mio nuovo xml con le informazioni sull'immagine
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
                            hasAnnotations = 'True'
                            for c in child:
                                b1 = ET.SubElement(m2, c.tag)
                                b1.text = " "
                                for attr in c.attrib:
                                    b1.set(attr,c.attrib[attr])
                            
                        index = index + 1

            shutil.rmtree(taskPath)

        # scrivo sul file info.txt se ci sono annotazioni o meno
        info.write(hasAnnotations)
        info.close()

        tree = ET.ElementTree(rootDest)
        
        with open (annotationPath, "wb") as files :
            tree.write(files)
        
        epoch = time.time()
        
        f = open(path+"/dataset/info.txt", "r")
        hasAnnotations = f.read()

        foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)
    else:
        # se la cartella esiste vuol dire che ho gia i dati per eseguire il confronto
        # open and read the file after the appending:

        epoch = time.time()

        if not isExist:
            f = open(revPath+"/dataset/info.txt", "r")
            hasAnnotations = f.read()

            foIntegration.create_fo_dataset(str(epoch), revPath+"/dataset/", pred, predOrTruth, hasAnnotations)

        elif not isExistReverse:
            f = open(path+"/dataset/info.txt", "r")
            hasAnnotations = f.read()

            foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)
        
        if predOrTruth == "/":
            f = open(revPath+"/dataset/info.txt", "r")
            hasAnnotations = f.read()

            foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)


def compare_pred_truth(id, pred):
# prendo i nomi delle immagini che ho caricato su cvat
    images = dbquery.get_MVSxCVAT_byMVE(id)

    # prendo gli idMVS di una determinata predizione
    idsMVSpred = dbquery.get_prediction_ids(pred)
    tasks = []
    idsCVAT = []

    # mi salvo i task presi in considerazione nella predizione e i nomi delle immagini interessate
    for idMVSpred in idsMVSpred:
            for img in images:
                if idMVSpred in img[0]:
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    # cartella in cui ci andranno le immagini interessate
    imagesPath = "datasets/{}xTruth/dataset/images/".format(pred)
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    
    # creo la cartella se non esiste e creo il dataset
    if not isExist:
        os.makedirs(imagesPath)

        annotationPath = "datasets/{}xTruth/dataset/annotation.xml".format(pred)
        
        # file aggiuntivo usato per scriverci se un dataset ha annotazioni o meno (in caso di confronto gia esistente si va a pescare questa informazine)
        info = open("datasets/{}xTruth/dataset/info.txt".format(pred), "w")

        # Preparo il nuovo file xml con le annotazioni delle sole immagini che mi interessano
        rootDest = ET.Element("annotations")
        
        # aggiungo il tag con la versione
        m1 = ET.Element("version")
        m1.text = "1.1"
        rootDest.append(m1)
        
        index = 0

        # variabile che mi serve per sapere se il dataset sara di tipo cvat o immagini (nel caso in cui non ci sia un file xml da caricare)
        hasAnnotations = 'False'

        # per ogni task scarico in locale il dataset cvat corrispondente (immagini + file con annotazioni)
        for task in tasks:
            taskPath = "datasets/{}xTruth/task{}".format(pred, task)
            CVATapi.get_task_dataset(task, taskPath)

            # copio in un altra cartella le immagini che ci interessano 
            for idCVAT in idsCVAT:
                if os.path.exists(taskPath+"/images/"+idCVAT):
                    
                    shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)
            
            # prendo il file delle annotazioni scaricato da cvat e lo esamino
            annPath = taskPath+"/annotations.xml"

            tree = ET.parse(annPath)

            rootSource = tree.getroot()

            # controlo i tag 'image' e se l'attributo 'name' e' tra gli idsCVAT salvati prima allora aggiungo un elemento al mio nuovo xml con le informazioni sull'immagine
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
                            hasAnnotations = 'True'
                            for c in child:
                                b1 = ET.SubElement(m2, c.tag)
                                b1.text = " "
                                for attr in c.attrib:
                                    b1.set(attr,c.attrib[attr])
                            
                        index = index + 1

            shutil.rmtree(taskPath)

        # scrivo sul file info.txt se ci sono annotazioni o meno
        info.write(hasAnnotations)
        info.close()

        tree = ET.ElementTree(rootDest)
        
        # scrivo sul file xml
        with open (annotationPath, "wb") as files :
            tree.write(files)
    
    # open and read the file after the appending:
    f = open("datasets/{}xTruth/dataset/info.txt".format(pred), "r")
    hasAnnotations = f.read()

    # random legato al tempo: nome del dataset su fiftyone
    epoch = time.time()

    # creo il dataset su cvat e carico i valori numerici della predizione
    dataset = foIntegration.create_fo_dataset(str(epoch), "datasets/{}xTruth/dataset/".format(pred), pred, 'Truth', hasAnnotations)

    # prendo i dati della prediciton
    MVSpreds = dbquery.get_prediction(pred)
    # prendo le colonne della prediction 
    columns = dbquery.get_prediction_columns(pred)

    # vado a vedere quel e l'indice della colonna idSample
    for index, col in enumerate(columns):
        if col[0] == "IdSample":
            i = index

    # per ogni riga della prediction vado a prendere le righe della tabella TruthValues che hanno il campo IdTruth uguale all'idSample
    for MVSpred in MVSpreds:
        rows = dbquery.get_truth_values(MVSpred[i])
        # per ogni riga restituita da TruthValues vado a prendere i campi con le info sulla proprieta e aggiungo la proprieta al dataset
        for row in rows:
            if row[2] is not None:
                foIntegration.add_sample_field(dataset, row[1], "double", row[2], MVSpred[0])
            else:
                foIntegration.add_sample_field(dataset, row[1], "varchar", row[3], MVSpred[0])
            
    foIntegration.launch_app(dataset)

   
