import os
import shutil
from app import dbquery, CVATapi
import xml.etree.ElementTree as ET

"""
def compare_predictions_dd(id, pred1, pred2):

    images = dbquery.get_MVSxCVAT(id)
    tasks1 = get_tasks(pred1, id, images)
    tasks2 = get_tasks(pred2, id, images)
    folderPath = "datasets/{}x{}/task{}".format(pred1,pred2, id)
    
    for task1 in tasks1:
        if task1 in tasks2:
            CVATapi.get_task_dataset(task1, folderPath)

def get_tasks(pred, id, images):
    
    idsMVS = dbquery.get_prediction(pred)
    folderPath = "datasets/{}/dataset{}".format(pred, id)

    tasks = []
    for idMVS in idsMVS:
        for img in images:
            if idMVS in img[0]:
                if img[2] not in tasks:
                    tasks.append(img[2])
    
    return tasks
    #for t in tasks:
    #    CVATapi.get_task_dataset(t, folderPath)
"""
def compare_predictions(id, pred1, pred2):
    
    images = dbquery.get_MVSxCVAT(id)
    idsMVSpred1 = dbquery.get_prediction(pred1)
    idsMVSpred2 = dbquery.get_prediction(pred2)
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
    # controllo se la cartella esiste 
    isExist = os.path.exists(imagesPath)
    
    # creo la cartella se non esiste
    if not isExist:
        os.makedirs(imagesPath)

    annotationPath = "datasets/{}x{}/dataset/annotation.xml".format(pred1,pred2)

    for task in tasks:
        taskPath = "datasets/{}x{}/task{}".format(pred1,pred2, task)
        CVATapi.get_task_dataset(task, taskPath)
        
        for idCVAT in idsCVAT:
            if os.path.exists(imagesPath+idCVAT):
                print("OK")
                shutil.copy(imagesPath+idCVAT, imagesPath)
        
        annPath = taskPath+"/annotations.xml"

        tree = ET.parse(annPath)

        root = tree.getroot()
        for image in root.iter('image'):
            print(image.attrib)
            for poly in root.iter('polyline'):
                print(poly.attrib)

        #shutil.rmtree(taskPath)
     
    root = ET.Element("annotations")
      
    m1 = ET.Element("version")
    m1.text = "1.1"
    root.append(m1)
    for index, idCVAT in enumerate(idsCVAT): 
        m2 = ET.Element("image", id=str(index), name=idCVAT, width="2464", height="2056")
        m2.text = " "
        root.append(m2)
        
    b1 = ET.SubElement(m1, "brand")
    b1.text = "Redmi"
    b2 = ET.SubElement(m1, "price")
    b2.text = "6999"
      
    m2 = ET.Element("mobile")
    root.append (m2)
      
    c1 = ET.SubElement(m2, "brand")
    c1.text = "Samsung"
    c2 = ET.SubElement(m2, "price")
    c2.text = "9999"
      
    m3 = ET.Element("mobile")
    root.append (m3)
      
    d1 = ET.SubElement(m3, "brand")
    d1.text = "RealMe"
    d2 = ET.SubElement(m3, "price")
    d2.text = "11999"
    
    tree = ET.ElementTree(root)
    
    with open (annotationPath, "wb") as files :
        tree.write(files)