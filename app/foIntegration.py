import os
import fiftyone as fo
import ntpath
from app import dbquery
from dotenv import load_dotenv

load_dotenv()

export_dir_fo = os.getenv('EXPORT_DIR_FO')

def create_fo_dataset(id, path, pred, predOrTruth, hasAnnotations):
    # cartella con le immagini
    data_path = path + "images/"

    if predOrTruth == 'Truth':
        labels_path2 = path + "annotationTruth.xml"
        label_field2 = "Truth"
    elif predOrTruth != '/':
        labels_path2 = path + "annotationPred2.xml"
        label_field2 = str(predOrTruth)

    # file con annotazioni xml
    labels_path = path + "annotationPred1.xml"

    export_dir = "/home/musausr/fiftyone/datasets_generated/" + id

    if hasAnnotations["pred1"] == 'True' and hasAnnotations["predOrTruth"] == 'True':
        # importo il dataset con immagini e annotazioni
        dataset = fo.Dataset.from_dir(
            dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
            label_field=str(pred),
            data_path=data_path,
            labels_path=labels_path,
            include_id=True,
            name=id
        )
        if predOrTruth != '/':
            # Merge in predictions
            dataset.merge_dir(
                data_path=data_path,
                labels_path=labels_path2,
                dataset_type=fo.types.CVATImageDataset,
                label_field=label_field2,
            )
        
        # esporto il dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.CVATImageDataset
        )
    elif hasAnnotations["pred1"] == 'True' and hasAnnotations["predOrTruth"] == 'False':
        # importo il dataset con immagini e annotazioni
        dataset = fo.Dataset.from_dir(
            dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
            label_field=str(pred),
            data_path=data_path,
            labels_path=labels_path,
            include_id=True,
            name=id
        )
        
        # esporto il dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.CVATImageDataset
        )
    elif hasAnnotations["pred1"] == 'False' and hasAnnotations["predOrTruth"] == 'True':
        # importo il dataset con immagini e annotazioni
        dataset = fo.Dataset.from_dir(
            dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
            label_field=label_field2,
            data_path=data_path,
            labels_path=labels_path2,
            include_id=True,
            name=id
        )
        
        # esporto il dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.CVATImageDataset
        )
    else:
        # importo il dataset con sole immagini
        dataset = fo.Dataset.from_dir(
            dataset_dir=data_path,
            dataset_type=fo.types.ImageDirectory,
            name=id
        )
        
        # esporto il dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.ImageDirectory
        )

    get_numeric_data(dataset, pred, 'idMVS')

    # se il confronto è tra predizione e verita
    if predOrTruth == 'Truth':
        return dataset
   
    # se predOrTruth è uguale a / significa che non è un confronto ma la visualizzazione di una sola predizione
    if predOrTruth != "/":
        get_numeric_data(dataset, predOrTruth, 'idMVS')

    # lancio l'app fiftyone 
    session = fo.launch_app(dataset)

def get_numeric_data(dataset, pred, filepathfield):

    columns = dbquery.get_columns_name_table(pred)
    
    datatype = dbquery.get_columns_type_table(pred)
   
    # loop per aggiungere i campi nel dataset fiftyone (uguali al nome delle colonne della tabella predictionX)
    excluded_field = []
    for index, x in enumerate(columns):
        if (x[0] != filepathfield):
            if (datatype[index][0] == 'float' or datatype[index][0] == 'double'):
                dataset.add_sample_field(x[0]+"_"+pred, fo.FloatField)
            elif (datatype[index][0] == 'int' or datatype[index][0] == 'bigint'):
                dataset.add_sample_field(x[0]+"_"+pred, fo.IntField)
            elif (datatype[index][0] == 'varchar'):
                dataset.add_sample_field(x[0]+"_"+pred, fo.StringField)
            else:
                excluded_field.append(x[0])

    # prendo tutti i campi della tabella prediction
    predictions = dbquery.get_prediction(pred)
    
    # aggiungo il valore preso dalle righe ai campi appena creati nel dataset
    with fo.ProgressBar() as pb:
        for sample in pb(dataset):
            i = 0
            sampleFilePath = sample.filepath
            headfp, tailfp = ntpath.split(sampleFilePath)

            for x in predictions: 
                if (x[0] in tailfp):
                    for z in columns:
                        if (z[0] != filepathfield) and (z[0] not in excluded_field):
                            field = z[0]+"_"+pred
                            sample[field] = x[i]
                        i = i + 1
            sample.save() 

def add_sample_field(dataset, name_field, type_field, value_field, idMVS):
    
    # aggiungo il campo passato come parametro al dataset fiftyone (controllo il tipo)
    if (type_field == 'float' or type_field == 'double'):
        dataset.add_sample_field(name_field+"_Truth", fo.FloatField)
    elif (type_field == 'int' or type_field == 'bigint'):
        dataset.add_sample_field(name_field+"_Truth", fo.IntField)
    elif (type_field == 'varchar'):
        dataset.add_sample_field(name_field+"_Truth", fo.StringField)
    else:
        excluded_field = name_field
    
    # aggiungo il valore passato come parametro al campo appena creato
    with fo.ProgressBar() as pb:
        for sample in pb(dataset):
            sampleFilePath = sample.filepath
            headfp, tailfp = ntpath.split(sampleFilePath)
            if (idMVS in tailfp):
                field = name_field+"_Truth"
                sample[field] = value_field
            sample.save() 

def launch_app(dataset):
    session = fo.launch_app(dataset)