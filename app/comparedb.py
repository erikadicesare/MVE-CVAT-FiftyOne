import json
import os
import re
import shutil
from app import dbquery, CVATapi, foIntegration
import xml.etree.ElementTree as ET    
import time
from PIL import Image

def view_prediction(id, pred):
    # prendo i nomi delle immagini che ho caricato su cvat
    images = dbquery.get_MVSxCVAT_byMVE(id)

    # prendo gli idMVS di una determinata predizione
    idsMVSpred = dbquery.get_prediction_ids(pred)
    idsMVS = []
    tasks = []
    idsCVAT = []

    # mi salvo i task presi in considerazione nella predizione e i nomi delle immagini interessate
    for idMVSpred in idsMVSpred:
            for img in images:
                if idMVSpred in img[0]:
                    idsCVAT.append(img[0])
                    idsMVS.append(idMVSpred)
                    if img[2] not in tasks:
                        tasks.append(img[2])

    path = "datasets/{}".format(pred)
    revPath = "datasets/{}".format(pred)
   
    dataset = get_data(path, revPath, tasks, idsCVAT, idsMVS, pred, "/")
    
    return dataset 

def compare_predictions(id, pred1, pred2):
    
    # prendo le immagini che ho caricato su cvat
    # prendo gli idMVS delle due prediction
    images = dbquery.get_MVSxCVAT_byMVE(id)
    idsMVSpred1 = dbquery.get_prediction_ids(pred1)
    idsMVSpred2 = dbquery.get_prediction_ids(pred2)
    idsMVS = []
    tasks = []
    idsCVAT = []
    # mi salvo i task presenti in entrambe le prediction e gli idsCVAT delle immagini condivise da entrambe le prediction 
    for idMVSpred1 in idsMVSpred1:
        if idMVSpred1 in idsMVSpred2:
            for img in images:
                if idMVSpred1 in img[0]:
                    idsMVS.append(idMVSpred1)
                    idsCVAT.append(img[0])
                    if img[2] not in tasks:
                        tasks.append(img[2])

    path = "datasets/{}x{}".format(pred1,pred2)
    revPath = "datasets/{}x{}".format(pred2,pred1)
    
    dataset = get_data(path, revPath, tasks, idsCVAT, idsMVS, pred1, pred2)

    return dataset 

def get_data(path, revPath, tasks, idsCVAT, idsMVS, pred, predOrTruth):

    ########## SE IDSCVAT E' VUOTO MANDA UN MESSAGGIO 
    if idsCVAT != []:

        # cartella in cui ci andranno le immagini interessate
        imagesPath = path+"/dataset/images/"
        imagesPathReverse = revPath+"/dataset/images/"
        # controllo se la cartella esiste 
        isExist = os.path.exists(imagesPath)
        isExistReverse = os.path.exists(imagesPathReverse)
        
        # creo la cartella se non esiste e creo il dataset
        if not isExist and not isExistReverse:
            os.makedirs(imagesPath)
            
            # file aggiuntivo usato per scriverci se un dataset ha annotazioni o meno (in caso di confronto gia esistente si va a pescare questa informazine)
            info = open(path+"/dataset/info.json", "w")

            index = 0
            hasAnnotations = {
                'pred1':'False',
                'predOrTruth': 'False'
            }

            # per ogni task scarico in locale il dataset cvat corrispondente (immagini + file con annotazioni)
            for task in tasks:
                taskPath = path+"/task{}".format(task)
                CVATapi.get_task_dataset(task, taskPath)
                
                # copio in un altra cartella le immagini che ci interessano 
                for idCVAT in idsCVAT:
                    if os.path.exists(taskPath+"/images/"+idCVAT):
                        
                        shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)

                shutil.rmtree(taskPath)

            # prendo le colonne e il loro tipo della prima predizione selezionata 
            columns = dbquery.get_columns_name_table(pred)
            datatype = dbquery.get_columns_type_table(pred)
            text_column = []
            
            # per ogni colonna/tipo se il tipo e' "text" la aggiungo alla lista text_column
            for col, dtype in zip(columns, datatype):
                if dtype[0] == "text":
                    text_column.append(col[0])
            
            # creo un file xml vuoto
            annotationPathPred1 = path+"/dataset/annotationPred1.xml"
            fxml = open(annotationPathPred1, "x")

            # scrivo nel file appena creato i tag seguenti
            fxml.write('<annotations><version>1.1</version>')

            # per ogni idsMVS:
            for i, idMVS in enumerate(idsMVS):
                
                # prendo l'immagine a cui fanno riferimento e scrivo nel file un tag <image> con alcuni attributi
                img = Image.open(path+"/dataset/images/"+idsCVAT[i])

                fxml.write('<image id="{}" name="{}" width="{}" height="{}">'.format(index, idsCVAT[i], img.width, img.height))
                
                # prendo la riga della prediction con l'id corrente (nb prendo solo i valori delle colonne di tipo "text", 
                # cioe quelle che hanno dei tag al loro interno come valore)
                if text_column != []:
                    row = dbquery.get_prediction_by_id(pred, idMVS, text_column)

                # per ogni valore della riga faccio un controllo ulteriore, cioe guardo se effettivamente soddisfano la regex 
                # per i tag, poi li scrivo nel file xml
                    for r in row[0]:
                        xml_string = str(r).replace('\u00A0',' ')
                        if re.match(r"(<.[^(><)]+>)", xml_string): 
                            hasAnnotations["pred1"] = 'True' 
                            fxml.write(xml_string)

                fxml.write('</image>')

                index = index + 1
            
            fxml.write('</annotations>')
            fxml.close()

            # se siamo nel caso in cui sto confrontando due predizioni, faccio la stessa cosa per la seconda predizione
            if predOrTruth != "/":
                # prendo le colonne e il loro tipo della prima predizione selezionata 
                columns = dbquery.get_columns_name_table(predOrTruth)
                datatype = dbquery.get_columns_type_table(predOrTruth)
                text_column_pred2 = []

                # per ogni colonna/tipo se il tipo e' "text" la aggiungo alla lista text_column_pred2
                for col, dtype in zip(columns, datatype):
                    if dtype[0] == "text":
                        text_column_pred2.append(col[0])
                
                # creo un file xml vuoto
                annotationPathPred2 = path+"/dataset/annotationPred2.xml"
                fxml2 = open(annotationPathPred2, "x")
                
                # scrivo nel file appena creato i tag seguenti
                fxml2.write('<annotations><version>1.1</version>')

                # per ogni idsMVS:
                for i, idMVS in enumerate(idsMVS):
                    
                    # prendo l'immagine a cui fanno riferimento e scrivo nel file un tag <image> con alcuni attributi
                    img = Image.open(path+"/dataset/images/"+idsCVAT[i])

                    fxml2.write('<image id="{}" name="{}" width="{}" height="{}">'.format(index, idsCVAT[i], img.width, img.height))

                    # prendo la riga della prediction con l'id corrente (nb prendo solo i valori delle colonne di tipo "text", 
                    # cioe quelle che hanno dei tag al loro interno come valore)
                    if text_column_pred2 != []:
                        row = dbquery.get_prediction_by_id(predOrTruth, idMVS, text_column_pred2)

                        for r in row[0]:
                            xml_string = str(r).replace('\u00A0',' ')
                            if re.match(r"(<.[^(><)]+>)", xml_string): 
                                hasAnnotations["predOrTruth"] = 'True' 
                                fxml2.write(xml_string)

                    fxml2.write('</image>')

                    index = index + 1
                
                fxml2.write('</annotations>')
                fxml2.close()

            # scrivo sul file info.txt se ci sono annotazioni o meno

            info.write(json.dumps(hasAnnotations))
            info.close()
            
            epoch = time.time()
            
            f = open(path+"/dataset/info.json", "r")
            hasAnnotations = json.load(f)
            f.close()

            return foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)
        else:
            # se la cartella esiste vuol dire che ho gia i dati per eseguire il confronto
            # open and read the file after the appending:

            epoch = time.time()

            if not isExist:
                f = open(revPath+"/dataset/info.json", "r")
                hasAnnotations = json.load(f)
                f.close()

                return foIntegration.create_fo_dataset(str(epoch), revPath+"/dataset/", pred, predOrTruth, hasAnnotations)

            elif not isExistReverse:
                f = open(path+"/dataset/info.json", "r")
                hasAnnotations = json.load(f)
                f.close()

                return foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)
            
            if predOrTruth == "/":
                f = open(revPath+"/dataset/info.json", "r")
                hasAnnotations = json.load(f)
                f.close()

                return foIntegration.create_fo_dataset(str(epoch), path+"/dataset/", pred, predOrTruth, hasAnnotations)
        

def compare_pred_truth(id, pred):
# prendo i nomi delle immagini che ho caricato su cvat
    images = dbquery.get_MVSxCVAT_byMVE(id)

    # prendo gli idMVS di una determinata predizione
    idsMVSpred = dbquery.get_prediction_ids(pred)
    idsMVS = []
    tasks = []
    idsCVAT = []

    # mi salvo i task presi in considerazione nella predizione e i nomi delle immagini interessate
    for idMVSpred in idsMVSpred:
            for img in images:
                if idMVSpred in img[0]:
                    idsCVAT.append(img[0])
                    idsMVS.append(idMVSpred)
                    if img[2] not in tasks:
                        tasks.append(img[2])

    # cartella in cui ci andranno le immagini interessate
    imagesPath = "datasets/{}xTruth/dataset/images/".format(pred)
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    
    # creo la cartella se non esiste e creo il dataset
    if not isExist:
        os.makedirs(imagesPath)

        annotationPath = "datasets/{}xTruth/dataset/annotationTruth.xml".format(pred)
        
        # file aggiuntivo usato per scriverci se un dataset ha annotazioni o meno (in caso di confronto gia esistente si va a pescare questa informazine)
        info = open("datasets/{}xTruth/dataset/info.json".format(pred), "w")

        # Preparo il nuovo file xml con le annotazioni delle sole immagini che mi interessano
        rootDest = ET.Element("annotations")
        
        # aggiungo il tag con la versione
        m1 = ET.Element("version")
        m1.text = "1.1"
        rootDest.append(m1)
        
        index = 0

        # variabile che mi serve per sapere se il dataset sara di tipo cvat o immagini (nel caso in cui non ci sia un file xml da caricare)
        hasAnnotations = {
            'pred1':'False',
            'predOrTruth': 'False'
        }

        # per ogni task scarico in locale il dataset cvat corrispondente (immagini + file con annotazioni)
        for task in tasks:
            taskPath = "datasets/{}xTruth/task{}".format(pred, task)
            CVATapi.get_task_dataset(task, taskPath)

            # copio in un altra cartella le immagini che ci interessano 
            for idCVAT in idsCVAT:
                if os.path.exists(taskPath+"/images/"+idCVAT):
                    
                    shutil.copy(taskPath+"/images/"+idCVAT, imagesPath)
            
        ## CREAZIONE FILE XML TRUTH ##
        #######################################################################################################################

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

                        # se il tag <image> ha al suo interno altri tag, li vado a prendere
                        if len(child) != 0:
                            hasAnnotations["predOrTruth"]='True'
                            for c in child:
                                b1 = ET.SubElement(m2, c.tag)
                                b1.text = " "
                                for attr in c.attrib:
                                    b1.set(attr,c.attrib[attr])
                            
                        index = index + 1

            shutil.rmtree(taskPath)

        ## CREAZIONE FILE XML PREDIZIONE ##
        #######################################################################################################################
        
        # prendo le colonne e il loro tipo della prima predizione selezionata 
        columns = dbquery.get_columns_name_table(pred)
        datatype = dbquery.get_columns_type_table(pred)
        text_column = []

        # per ogni colonna/tipo se il tipo e' "text" la aggiungo alla lista text_column
        for col, dtype in zip(columns, datatype):
            if dtype[0] == "text":
                text_column.append(col[0])

        # creo un file xml vuoto
        annotationPathPred = "datasets/{}xTruth/dataset/annotationPred1.xml".format(pred)
        fxml = open(annotationPathPred, "x")
        
        # scrivo nel file appena creato i tag seguenti
        fxml.write('<annotations><version>1.1</version>')

        # per ogni idsMVS:
        for i, idMVS in enumerate(idsMVS):

            # prendo l'immagine a cui fanno riferimento e scrivo nel file un tag <image> con alcuni attributi
            img = Image.open("datasets/{}xTruth/dataset/images/".format(pred)+idsCVAT[i])

            fxml.write('<image id="{}" name="{}" width="{}" height="{}">'.format(index, idsCVAT[i], img.width, img.height))
            
            # prendo la riga della prediction con l'id corrente (nb prendo solo i valori delle colonne di tipo "text", 
            # cioe quelle che hanno dei tag al loro interno come valore)
            if text_column != []:
                row = dbquery.get_prediction_by_id(pred, idMVS, text_column)

                for r in row[0]:
                    xml_string = str(r).replace('\u00A0',' ')
                    if re.match(r"(<.[^(><)]+>)", xml_string): 
                        hasAnnotations["pred1"]='True'
                        fxml.write(xml_string)

            fxml.write('</image>')

            index = index + 1
        
        fxml.write('</annotations>')
        fxml.close()

        ######################################################################################################################

        # scrivo sul file info.txt se ci sono annotazioni o meno
        info.write(json.dumps(hasAnnotations))
        info.close()

        tree = ET.ElementTree(rootDest)
        
        # scrivo sul file xml
        with open (annotationPath, "wb") as files :
            tree.write(files)
    
    # open and read the file after the appending:
    f = open("datasets/{}xTruth/dataset/info.json".format(pred), "r")
    hasAnnotations = json.load(f)
    f.close()
    
    # random legato al tempo: nome del dataset su fiftyone
    epoch = time.time()
    
    # creo il dataset su cvat e carico i valori numerici della predizione
    dataset = foIntegration.create_fo_dataset(str(epoch), "datasets/{}xTruth/dataset/".format(pred), pred, 'Truth', hasAnnotations)

    # prendo i dati della prediciton
    MVSpreds = dbquery.get_prediction(pred)
    # prendo le colonne della prediction 
    columns = dbquery.get_columns_name_table(pred)

    # vado a vedere quel e l'indice della colonna idSample
    for index, col in enumerate(columns):
        if col[0] == "IdSample":
            i = index

    # per ogni riga della prediction vado a prendere le righe della tabella TruthValues che hanno il campo IdSample uguale all'idSample
    for MVSpred in MVSpreds:
        rows = dbquery.get_truth_values(MVSpred[i])
        # per ogni riga restituita da TruthValues vado a prendere i campi con le info sulla proprieta e aggiungo la proprieta al dataset
        for row in rows:
            if row[2] is not None:
                foIntegration.add_sample_field(dataset, row[1], "double", row[2], MVSpred[0])
            else:
                foIntegration.add_sample_field(dataset, row[1], "varchar", row[3], MVSpred[0])
            
    #foIntegration.launch_app(dataset)
    return dataset 

# funzione usata per avere una lista di confronti fatti in passato (per uno specifico progetto mve)
def get_comparisons(idMVE):

    predictions = dbquery.get_predList_ids(idMVE)

    root='datasets'
    dirlist = [ item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item)) ]
    dirlist.sort(key=lambda f: os.path.getmtime(os.path.join(root, f)), reverse=True)
    comparisons = []
    i = len(dirlist)
    for dir_name in dirlist:
        if "Truth" in dir_name:
            compare = dir_name.split("x")
            if compare[0] in predictions:
                dir_type = "Predizione vs Verità"
                comp = {
                    "index": i,
                    "dir_type": dir_type,
                    "compare": compare,
                    "dir_name": dir_name
                }
                comparisons.append(comp)
        elif "x" not in dir_name:
            if dir_name in predictions:
                dir_type = "Predizione"
                comp = {
                    "index": i,
                    "dir_type": dir_type,
                    "compare": dir_name,
                    "dir_name": dir_name
                }
                comparisons.append(comp)
        else:
            compare = dir_name.split("x")
            if compare[0] in predictions:
                dir_type = "Predizione vs Predizione"
                comp = {
                    "index": i,
                    "dir_type": dir_type,
                    "compare": compare,
                    "dir_name": dir_name
                }
                comparisons.append(comp)
    
        i = i - 1 
    return comparisons
