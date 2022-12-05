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
    # in caso affermativo vado ad aggiornare le proprieta in truthValue (elimino quelle 
    # esistenti e aggiungo quelli nuovi)
    sampleIdNames = dbquery.get_sampleIdNames_truth_MVE(idMVE)
    for sample in sampleIdNames:
        if data[col][i] == sample['name']:
            updated = i
            dbquery.delete_truth_value(sample['id'])
            idTruth = sample['id']
            break

        else:
            updated = None

    if updated is None:
        idTruth = dbquery.insert_truth(idMVE, data[col][i]) 
            
    propsName = []
    valuesReal = []
    valuesString = []

    for column in columns:
        if (column != col): 
            if (pd.isnull(data[column][i]) != True):
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
    # cancello i file che sono stati scaricati in precedenza
    for filename in os.listdir('download/truth'):
        os.remove("download/truth/"+filename)

    # prendo le righe della tabella Truth corrispondenti ad un determinato progetto MVE
    # quindi ogni riga restituita da questa funzione avra un idSample, un idMVE e un nome
    truth = dbquery.get_truth_mve(idMVE)

    # per ogni riga restituita vado a prendere i nomi delle proprieta presenti nella 
    # tabella TruthValues (che fanno riferimento allo stesso idSample/idTruth).
    # creo una lista con tutti i nomi delle proprieta esistenti in quel progetto MVE
    columns = ['Name']
    for tr in truth:
        values = dbquery.get_truth_prop_names(tr[0])
        for val in values:
            if val[0] not in columns:
                columns.append(val[0])
    
    # per ogni riga restituita dalla query sulla tabella Truth, creo una lista row 
    # inizializzata a None per ogni colonna presente nella lista columns. 
    # poi per ogni riga presa dalla tabella TruthValues con idTruth=idSample corrente
    # vado a prendere la posizione della colonna nella lista columns per poi andare a 
    # cabiare il valore None nella lista row in quella posizione. controllo anche che 
    # il valore in posizine 2 sia diverso da None: in caso affermativo cambio con quel
    # valore, altrimenti con il valore in posizine 3 (pos 2 = valore reale, pos 3 = 
    # valore stringa)  
    rows = []
    for tr in truth:
        row = []
        for col in columns:
            row.append(None)
        row[0] = tr[2]
        values = dbquery.get_truth_values(tr[0])
        for val in values:
            if val[1] in columns:
                index = columns.index(val[1])
                if val[2] is not None:
                    row[index] = val[2]
                else:
                    row[index] = val[3]
        rows.append(row)
    # creo il dataframe che poi converto in csv
    df = pd.DataFrame(data=rows, columns=columns)
    namefile = "download/truth/MVEproject"+idMVE+".csv"
    df.to_csv(namefile, index=False, header=True)
    return namefile