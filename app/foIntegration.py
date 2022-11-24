import fiftyone as fo
import mysql.connector
from mysql.connector import errorcode
import ntpath
from app import dbquery

def create_fo_dataset(id, path, pred1, pred2, hasAnnotations):
    # The directory containing the source images
    #data_path = "../task45/images/"
    data_path = path + "images/"

    # The path to the COCO labels JSON file
    #labels_path = "../task45/annotations.xml"
    labels_path = path + "annotation.xml"

    export_dir = "/home/musausr/fiftyone/datasets_generated/" + id

    if hasAnnotations == 'True':
        # Import the dataset
        dataset = fo.Dataset.from_dir(
            dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
            label_field="prediction",
            data_path=data_path,
            labels_path=labels_path,
            include_id=True,
            name=id
        )

        # Export the dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.CVATImageDataset
        )
    else:
        # Import the dataset
        dataset = fo.Dataset.from_dir(
            dataset_dir=data_path,
            dataset_type=fo.types.ImageDirectory,
            name=id
        )

        # Export the dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.ImageDirectory
        )

    get_numeric_data(dataset, pred1, 'idMVS')
    if pred2 != "/":
        get_numeric_data(dataset, pred2, 'idMVS')
 

    session = fo.launch_app(dataset)


def create_fo_dataset_truth(id, path, pred, hasAnnotations):
    # The directory containing the source images
    #data_path = "../task45/images/"
    data_path = path + "images/"

    # The path to the COCO labels JSON file
    #labels_path = "../task45/annotations.xml"
    labels_path = path + "annotation.xml"

    export_dir = "/home/musausr/fiftyone/datasets_generated/" + id

    if hasAnnotations == 'True':
        # Import the dataset
        dataset = fo.Dataset.from_dir(
            dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
            label_field="prediction",
            data_path=data_path,
            labels_path=labels_path,
            include_id=True,
            name=id
        )

        # Export the dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.CVATImageDataset
        )
    else:
        # Import the dataset
        dataset = fo.Dataset.from_dir(
            dataset_dir=data_path,
            dataset_type=fo.types.ImageDirectory,
            name=id
        )

        # Export the dataset
        dataset.export(
            export_dir=export_dir,
            dataset_type=fo.types.ImageDirectory
        )
    get_numeric_data(dataset, pred, 'idMVS')

    return dataset

def get_numeric_data(dataset, pred, filepathfield):

    columns = dbquery.get_columns_name_table(pred)
    
    datatype = dbquery.get_columns_type_table(pred)
   
    # loop to add the fields (equal to the name of the columns)

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

    predictions = dbquery.get_prediction(pred)
    
    # Add numeric values taken from the rows to the field just created 
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
    
    if (type_field == 'float' or type_field == 'double'):
        dataset.add_sample_field(name_field+"_Truth", fo.FloatField)
    elif (type_field == 'int' or type_field == 'bigint'):
        dataset.add_sample_field(name_field+"_Truth", fo.IntField)
    elif (type_field == 'varchar'):
        dataset.add_sample_field(name_field+"_Truth", fo.StringField)
    else:
        excluded_field = name_field
    
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