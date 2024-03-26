# Smart Assistance API
Python backend API for the web application.

---

### Overview
This repository contains backend API code forSmart Assistance tools. It is written in Python, built on Flask and PostgreSQL.

### Requirements
- Docker desktop 4.12.0 or the latest docker CLI
### Directory Structure
**run.py** : Main script that runs the API.
**manage.py** Script for database initializer (migration)

**src/** : Application code folder.


- **controllers/** : Route details of files
  
- **models/** : Data Models for SQLAlchemy
  
- **services/** : Mainly database related services for route handlers

**tests/** : Unit testing scripts.

> **Warning**
> Running these services can add dummy data to production. Verify and Run.

**dev-requirements.txt** : All python packages required to build the docker image for development
**prod-requirements.txt** : All python packages required to build the docker image for **PRODUCTION**

**runtime.env.template** : Template file containing all ENV variables to run container

**docker-compose.yml** : Docker compose configuration files for running posrgres server, database migration and the API containers
migration pgadmin in a docker container in [detached mode](https://www.devopsschool.com/blog/detached-d-mode-in-docker-explained/). You can skip this part if you are comfortable with using raw PostgreSQL in the CLI.
Assume you have not run pgadmin on docker before, you can pull the pgadmin image from docker and run it with default parameters with 
`docker run -p 5050:80 -e 'PGADMIN_DEFAULT_EMAIL=pgadmin4@pgadmin.org' -e 'PGADMIN_DEFAULT_PASSWORD=admin' -d --name pgadmin4 dpage/pgadmin4`
In short, the command above pulls the pgadmin4 image from docker and run it in a container with port number 5050, you can change the email and password if you wish to. The image would be named dpage/pgadmin4 on your computer.
Now you should see the container is running. Do `docker ps` to check running containers. Now you should be able to access pgadmin at http://localhost:5050/login
Proceed to login with credentials provided in the command above. 
#### Configure .env file
Create a .env file from the runtime.env.template, You will need to change the `DATABASE_URI` to `postgres://postgres:postgrespw@postgres/smart_assistance_db`

> This URI is based on values picked up from the postgres service in docker-compose.yml

**List of ENV variables required to run the containers**
- `PORT` : Port at which app runs.
- `DATABASE_URI`: For database connection
- `JWT_KEY`: Secret key for encryption
- `CORS_ORIGIN` : Origin for resource sharing. eg: '*'
You may need to reach out to other developers for certain values required to run the API should you encounter any ENV error.
#### Start Postgres Database
Now do `docker compose up` to build the images.
Now you should be able to visit http://localhost:5000/v1/. Great, but the API is not connected to a database yet. You may have noticed the "migration" container exited with error, hence now we need to set up the postgresql server for database migration.
#### Set up DB pre-requisites
Basically we need to create a server and inside the server create a schema named **cs_cognicept**. You may skip this part if you know how to create a server and schema without pgadmin.
Previously we have pgadmin container running in the background, and after running docker compose we have our postgres container up and running.
After logging in pgadmin, click on add new server, give it a name, and go to the connection tab and enter the following configurations.
##### For MacOs/Windows
Use `host.docker.internal` as Host name/address
![pgadmin](img/pgadmin.png)

##### For Linux
Use a static local host ip, usually `172.17.0.1`.
![pgadminlinux](img/linuxpgadmin.jpg)
If the ip above does not work, you may need to double check what is the ip on your linux system by running `hostip=$(ip route show | awk '/default/ {print $3}')` followed by `echo $hostip`

Now create a new database in the server we created previously, and in this database create a new schema named **cs_cognicept**
![schema](img/schema_cs_.png)
The format for the database url is `postgres://UserName:Password@YourHostname:5432/DatabaseName`

#### Migrating the database
make the initiate migration for the DB with the following commands: 

`$ docker compose run migration`

#### Launch Application
Finally, restart the docker compose by doing `docker compose down` followed by `docker compose up` (`docker-compose up/down` on linux). The first time running this compose is to create the images from the dockerfiles and run the containers as configured in docker-compose.yml. The second time running this compose is to complete the migration and get everything up and running properly.

### Celery worker

`$ pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`

`$ celery -A src.celery_app worker --loglevel=info -P threads`

`--concurrency=10`
---
### How to build

sudo docker build -f Dockerfile.prod -t meetingx-backend .

docker tag meetingx-backend registry.digitalocean.com/meetingx/meetingx-backend

docker push registry.digitalocean.com/meetingx/meetingx-backend

### 

kubectl exec meetingx-api-85bbf9d7bd-bhxsf -- cat /var/log/uwsgi/uwsgi.log

### Usage
#### Swagger
When everything is up and running properly, the API can be accessed through Swagger at http://localhost:{PORT}/v1/
![api](/img/api.png)


### Redis Guide

** Please be patient while the chart is being deployed **

Redis&reg; can be accessed on the following DNS names from within your cluster:

    my-redis-master.default.svc.cluster.local for read/write operations (port 6379)
    my-redis-replicas.default.svc.cluster.local for read-only operations (port 6379)



To get your password run:

    export REDIS_PASSWORD=$(kubectl get secret --namespace default my-redis -o jsonpath="{.data.redis-password}" | base64 -d)

To connect to your Redis&reg; server:

1. Run a Redis&reg; pod that you can use as a client:

   kubectl run --namespace default redis-client --restart='Never'  --env REDIS_PASSWORD=$REDIS_PASSWORD  --image docker.io/bitnami/redis:7.2.3-debian-11-r2 --command -- sleep infinity

   Use the following command to attach to the pod:

   kubectl exec --tty -i redis-client \
   --namespace default -- bash

2. Connect using the Redis&reg; CLI:
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h my-redis-master
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h my-redis-replicas

To connect to your database from outside the cluster execute the following commands:

  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
        Watch the status with: 'kubectl get svc --namespace default -w my-redis'

    export SERVICE_IP=$(kubectl get svc --namespace default my-redis-master --template "{{ range (index .status.loadBalancer.ingress 0) }}{{ . }}{{ end }}")
    REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h $SERVICE_IP -p 6379

### Celery
celery -A src.celery beat --loglevel=info
celery -A src.celery worker  --loglevel=info --concurrency=1 -P eventlet

### Release Notes
- 1.0.0 [10/12/2023]
    - Init Source Code


