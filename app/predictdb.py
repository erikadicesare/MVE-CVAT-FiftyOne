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

    # Se la colonna con il sampleId non esiste, restituisco un errore
    stringSampleId = 'sampleid'
    stringIdSample = 'idsample'
    stringSampleName = 'samplename'
    stringNameSample = 'namesample'

    columns = data.columns
    lower_columns = [column.lower() for column in columns]

    if ((stringSampleId.casefold() not in lower_columns) and (stringIdSample.casefold() not in lower_columns) and (stringSampleName.casefold() not in lower_columns) and (stringNameSample.casefold() not in lower_columns)):
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

    # inserisco una istanza nella tabela PredList con l'idPred (nome tabella Prediction), nome del file e id progetto mve corrispondente
    dbquery.insert_pred_list(idPred, file_name, idMVE)
        
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
        # salvo il nome della colonna contenente il sampleId (o il sampleName) e aggiungo la colonna nella tabella PredictionX
        # Il sampleName verra cercato nella tabella Truth e verra di conseguenza salvato l'id corrispondente
        if (column.lower() == stringIdSample.casefold() or column.lower() == stringSampleId.casefold() or column.lower() == stringNameSample.casefold() or column.lower() == stringSampleName.casefold()):
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
    
    # SE il campo individuato per il sample è l'id 
    if (stringSampleId.casefold() in lower_columns) or (stringIdSample.casefold() in lower_columns):


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

    # SE il campo individuato per il sample è in nome
    elif (stringNameSample.casefold() in lower_columns) or (stringSampleName.casefold() in lower_columns):
        # prendo i nomi dei sample presenti nella tabella Truth
        sampleNamesTruth = dbquery.get_sampleNames_truth()

        # per ogni riga del dataframe data, vado a prendere ogni valore per ogni colonna esistente.
        # Prima controllo se la colonna corrente è quella del Sample Name. In caso affermativo, 
        # se il nome esiste tra quelli della tabella Truth, vado a prendere l'id associato a quel nome
        for index, row in data.iterrows():
            currentRow = []
            for column in columns:
                if (column.lower() == stringNameSample.casefold() or column.lower() == stringSampleName.casefold()):
                    idSample = None
                    if (pd.isnull(row[column]) == False):
                        if row[column] in sampleNamesTruth:
                            idSample = dbquery.get_id_from_name_truth(row[column])
                            currentRow.append(idSample)
                        else:
                            currentRow.append(None)
                    else:
                        currentRow.append(None)
                else:
                    if (pd.isnull(row[column]) == False):
                        currentRow.append(row[column])
                    else:
                        currentRow.append(None)
                        
            if idSample in sampleIdsTruth: 
                dbquery.insert_prediction_row(idPred, currentRow)

    shutil.rmtree('tempPred{}'.format(uuid))

    return redirect(url_for('index'))

def download_pred(idMVE, pred):
    # cancello i file che sono stati scaricati in precedenza
    for filename in os.listdir('download/pred'):
        os.remove("download/pred/"+filename)

    # prendo i nomi delle colonne della tabella selezionata dall'utente 
    # e cambio la colonna con nome 'idMVS' con 'ObjKey' 
    dbcolumns = dbquery.get_prediction_columns(pred)
    columns = []
    for col in dbcolumns:
        if col[0] == 'idMVS':
            columns.append('ObjKey')
        else:
            columns.append(col[0])

    # prendo le righe della tabella selezionata 
    table = dbquery.get_prediction(pred)
    # creo il dataframe che poi converto in csv
    df = pd.DataFrame(table, columns=columns)
    namefile = "download/pred/"+pred+".csv"
    df.to_csv(namefile, index=False, header=True)
    return namefile