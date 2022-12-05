# cvatFiftyone

run cvat
```
export CVAT_HOST=<host_ipaddress>
docker-compose up -d
```

run fiftyone
```
cd fiftyone/fiftyone/server
python main.py
```

run  flask (optional `--port=<num_port>`)
```
$ flask run --host=0.0.0.0
```

run 

N.B. the file named "db_first_setup.py" (inside "app" folder) if runned with the command `python db_first_setup.py` will create a database named "MVE Database" with all the tables needed

N.B.2 the file .env has to be set or create if doesn't exist before running the command `flask run`

.env content:

```
USERNAME_CVAT=<cvat_username>
PASSWORD_CVAT=<cvat_password>
URL_CVAT=http://<your_host_with_port>/api #change it with the host of your cvat server
MAX_SIZE_LOAD_FILE=1000000000
USER_DB=root #change it with the user if different from root
NAME_DB=MVE Database
``` 
