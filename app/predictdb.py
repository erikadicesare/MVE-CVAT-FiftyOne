import math
import pandas as pd
import ntpath, os, shutil
from flask import make_response, redirect, render_template, request, url_for
from app import dbquery

# Leggo file csv o xlsx 
def read_file(file, idMVE):

    uuid = request.form.get('uuid')

    pathFolder = 'tempPred{}'.format(uuid)

    # controllo se la cartella esiste 
    isExist = os.path.exists(pathFolder)
    
    # creo la cartella se non esiste
    if not isExist:
        os.makedirs(pathFolder)

    headfp, tailfp = ntpath.split(file.filename)
    
    pathFile = 'tempPred{}/'.format(uuid) + tailfp
    file.save(pathFile)
    

    # Leggo il file csv/xls
    file_name, file_extension = ntpath.splitext(tailfp)

    if (file_extension == ".csv"):
        data = pd.read_csv(filepath_or_buffer=pathFile)
    else:
        data=pd.read_excel(io=pathFile)

    columns = data.columns

    # Se la colonna con il sampleId non esiste, restituisco un errore
    if (('SampleId' not in columns) and ('SampleID' not in columns) and ('IdSample' not in columns)):
        shutil.rmtree('tempPred{}'.format(uuid))
        return make_response(render_template("404.html", info="Il file inserito non contiene un campo compatibile con IdSample"), 404)
    
    # La funzione count_table conta le tabelle esistenti nel db che hanno
    # come nome qualcosa uguale a "Prediction"
    count = dbquery.count_table()

    # idPred incrementa di uno rispetto all'ultima tabella Prediction inserita
    idPred = 'Prediction{}'.format(count+1)
    i = 1

    # Dato che sono possibili inserimenti simultanei da piu client, per evitare 
    # di avere due tabelle con lo stesso nome faccio prima un controllo
    status = dbquery.check_table_exists(idPred)
    while status:
        idPred = 'Prediction{}'.format(count+1+i)
        status = dbquery.check_table_exists(idPred)
        i = i + 1
    
    # Creao la tabella PredictionX
    dbquery.create_table_prediction(idPred)  

    # inserisco una istanza nella tabela PredList con l'idPred (nome tabella Prediction) e nome del file
    dbquery.insert_pred_list(idPred, file_name)
        
    # se esiste la colonna ObjKey allora quella avra gli idMVS; se non esiste prendo di default la prima colonna
    if 'ObjKey' in columns:
        idMVS = 'ObjKey'
    else:
        idMVS = data.iloc[:, 0]  

    
    # per ogni colonna vado a prendere il primo valore non nullo e guardo se è un numero 
    # o altro. In caso di altro assegnamo il tipo stringa
    # La funzione add_column_prediction aggiunge la colonna corrente (e il suo tipo) 
    # alla tabella Prediction appena crata
    
    for column in columns:
        allNull = True
        # salvo il nome della colonna contenente il sampleId e aggiungo la colonna nella tabella PredictionX
        if (column == 'SampleId' or column == 'SampleID' or column == 'IdSample'):
            col_sampleId = column
            dbquery.add_column_prediction_fk(idPred)
        elif (column != idMVS):
            for d in data[column]:
                if (pd.isnull(d) == False):
                    allNull = False
                    if ((isinstance(d, float)) or (isinstance(d, int))):
                        dataType = "DOUBLE"
                    else:
                        dataType = "VARCHAR(100)"
                    
                    dbquery.add_column_prediction(idPred, column, dataType)
                    break
            # se la colonna ha solo valori nulli la elimino
            if allNull == True:
                del data[column]
    
    columns = data.columns

    # prendo gli id dei sample presenti nella tabella Truth
    sampleIdsTruth = dbquery.get_sampleIds_truth()

    # per ogni riga del dataframe data, vado a prendere ogni valore per ogni colonna esistente.
    # controllo che il sampleId presente nella prediction sia esistente tra i sampleId Truth
    for index, row in data.iterrows():
        currentRow = []
        for column in columns:                    
            if (pd.isnull(row[column]) == False):
                currentRow.append(row[column])
            else:
                currentRow.append(None)
        if row[col_sampleId] in sampleIdsTruth:   
            dbquery.insert_prediction_row(idPred, currentRow)

    shutil.rmtree('tempPred{}'.format(uuid))

    return redirect(url_for('index'))

