import pandas as pd
import ntpath, os, shutil
from flask import request
from app import dbquery

# Leggo file csv o xlsx 
def read_file(file, idMVE):

    uuid = request.form.get('uuid')

    pathFolder = 'tempTruth{}'.format(uuid)

    # controllo se la cartella esiste 
    isExist = os.path.exists(pathFolder)
    
    # creo la cartella se non esiste
    if not isExist:
        os.makedirs(pathFolder)

    headfp, tailfp = ntpath.split(file.filename)
    
    pathFile = 'tempTruth{}/'.format(uuid) + tailfp
    file.save(pathFile)
    
    # Use pandas to read a excel file by prodiving the path of file
    # The output of read_excel() function here is stored as a DataFrame
    file_name, file_extension = ntpath.splitext(tailfp)

    if (file_extension == ".csv"):
        data = pd.read_csv(filepath_or_buffer=pathFile)
    else:
        data=pd.read_excel(io=pathFile)

    columns = data.columns
    
    # controllo se esiste una colonna 'Name', 'Nome', 'name' oppure 'nome'
    # se non esiste prendo la prima colonna
    # Per ogni valore presente nella colonna 'Name'/'Nome'/'name'/'nome' chiamo la funzione
    # create_row_truth_valus passandogli l'id del progetto MVE, il dataframe con i dati estratti
    # dal file csv/xls, l'indice i corrente (riga corrente), 'Name'/'Nome'/'name'/'nome', e la
    # lista con i nomi delle colonne
    updated = []
    if 'Name' in columns:
        for i in range(len(data['Name'])):
            insert = create_row_truth_values(idMVE, data, i, 'Name', columns)
            if insert is not None:
                updated.append(insert)
    elif 'Nome' in columns:
        for i in range(len(data['Nome'])):
            insert = create_row_truth_values(idMVE, data, i, 'Nome', columns)
            if insert is not None:
                updated.append(insert)
    elif 'name' in columns:
        for i in range(len(data['name'])):
            insert = create_row_truth_values(idMVE, data, i, 'name', columns)
            if insert is not None:
                updated.append(insert)
    elif 'nome' in columns:
        for i in range(len(data['nome'])):
            insert = create_row_truth_values(idMVE, data, i, 'nome', columns) 
            if insert is not None:
                updated.append(insert)
    else:
        for i in range(len(data.iloc[:, 0])):
            insert = create_row_truth_values(idMVE, data, i, data.columns[0], columns)
            if insert is not None:
                updated.append(insert)

    shutil.rmtree('tempTruth{}'.format(uuid))
    
    return updated

# creo tre oggetti: uno con i nomi delle proprieta, uno con i valori numerici delle proprieta e
# uno con i valori stringa delle proprieta 
# per ogni proprieta/valore numerico/valore stringa chiamo la funzione insert_truth_values dello
# script dbquery (che inserisce nel db una riga per ogni proprieta/valori con il corrispondente idTruth)

def create_row_truth_values(idMVE, data, i, col, columns):

    # Controllo se esiste gia una verita con il nome corrente dello specifico progetto mve
    # in caso affermativo prendo la riga del db corrispondente e la elimino, in modo da inserire quella nuova
    sampleNames = dbquery.get_sampleNames_truth_MVE(idMVE)
    for sampleName in sampleNames:
        print(i, data[col][i], sampleName)
        if data[col][i] == sampleName:
            dbquery.delete_truth(data[col][i])
            updated = i
            break
        else:
            updated = None
    
    idTruth = dbquery.insert_truth(idMVE, data[col][i]) 
    
    propsName = []
    valuesReal = []
    valuesString = []

    for column in columns:
        if (column != col): 
            propsName.append(column)
            if ((isinstance(data[column][i], float)) or (isinstance(data[column][i], int))):
                valuesReal.append(data[column][i])
            else:
                valuesReal.append(None)
            valuesString.append(str(data[column][i]))
    
    if (len(propsName) == len(valuesReal) and len(valuesReal) == len(valuesString)):
        for propName, valueReal, valueString in zip(propsName, valuesReal, valuesString):
            dbquery.insert_truth_values(idTruth, propName, valueReal, valueString)

    return updated

def download_truth(idMVE):
    print()