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


**Getting started with the API**

Almost of the API require access token, you will need to create an account and login with the authorization token.

Follow these steps bellow to create an account

Send request to http://localhost:{PORT}/web/v2/user/registration  
Method: POST  
JSON Body
```Json
{
  "email": "someone@gmail.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+916655928947",
  "password": "Admin@1234",
  "organization_name": "Smart Assistance Systems",
  "country_id": "4662f059-60eb-4a63-a568-98b92986ec68"
}
```

If everything work well, the response body with organization_id will return

```Json
{
  "organization_id": "2d747b63-47e7-4316-9c5d-72bee6f088ec"
}
```

When the account is ready. Upon logging in you should obtain the **access_token** from the response.

Send request to http://localhost:{PORT}/web/v2/user/login 
Method: POST  
Json body: 
```Json
{
  "username": "someone@gmail.com",
  "password": "KABAM123#"
}
```

If server response with status code 200 and response body contains **access_token**. That mean 
the user is login successfully

```Json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2ODkyMTUyOTcsIm5iZiI6MTY4OTIxNTI5NywianRpIjoiZWNhNDE2YTUtOWVjZC00OTA1LWI3MjItYWM2N2FlOGJjODI0IiwiZXhwIjoxNjg5ODIwMDk3LCJpZGVudGl0eSI6InNvbWVvbmVAZ21haWwuY29tIiwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIiwidXNlcl9jbGFpbXMiOnsidXNlcl9pZCI6ImY0NDc5OWNhLTM0Y2ItNGEzOS1iYjU5LTViYTFkZDEwNTYzMSIsInVzZXIiOiJzb21lb25lQGdtYWlsLmNvbSIsInJvbGUiOlt7InJvbGVfbmFtZSI6IkthYmFtIFN1cGVyIEFkbWluIiwicm9sZV9pZCI6ImI0MGVlMWFlLTVhMTItNDg3YS05OGNjLWI2ZDA3MjM4ZTE3YSJ9XSwicGVybWlzc2lvbnMiOlsicm9ib3RvcHM6dmlzaXQiLCJsb2dvdXQ6dmlzaXQiLCJ0aWNrZXRzOnZpc2l0IiwiZGFzaGJvYXJkOnZpc2l0Iiwic2V0dGluZ3M6dmlzaXQiLCJyb2JvdHM6dmlzaXQiLCJzaXRlczp2aXNpdCIsImNhbWVyYV93aWRnZXQ6dmlzaXQiLCJjb25uZWN0ZWRfdXNlcnM6dmlzaXQiLCJldmVudF9sb2dzOnZpc2l0IiwiZXZlbnRfbG9nczpkb3dubG9hZCIsInNvdW5kOnVzZSIsImFkbWluX3JvYm90X2FjdGlvbjp1c2UiLCJyZW5kZXJfbWVudTp2aXNpdCIsImxldmVsc19tZW51OnZpc2l0IiwibWFwX21lbnU6dmlzaXQiLCJtYXBzOmVkaXQiLCJtYXBfc3RyZWFtOnZpc2l0IiwiYW5ub3RhdGlvbnM6ZWRpdCIsImNhbWVyYTplZGl0IiwidG9waWNfbW9uaXRvcjp2aXNpdCIsInRlcm1pbmFsOnZpc2l0IiwidGlja2V0czplZGl0Iiwic2l0ZXM6ZWRpdCIsInJvYm90czplZGl0Iiwic2NoZWR1bGVzOmVkaXQiLCJtaXNzaW9uczplZGl0Iiwid2F5cG9pbnRzOmVkaXQiLCJzY2hlZHVsZXM6dmlzaXQiLCJtaXNzaW9uczp2aXNpdCIsIndheXBvaW50czp2aXNpdCIsInJvYm90X2FjdGlvbjp1c2UiLCJyb2JvdF90ZWxlb3A6dXNlIiwidXNlcnM6ZWRpdCIsInVzZXJzOnZpc2l0IiwidGlja2V0c19mbTp2aXNpdCIsImludGVybmFsX3VzZXI6dmlzaXQiXSwiZGVmYXVsdF9wYWdlIjoicm9ib3RvcHMiLCJwcm9maWxlX25hbWUiOiJKb2huIERvZSIsIm9yZ2FuaXphdGlvbl9pZCI6IjJkNzQ3YjYzLTQ3ZTctNDMxNi05YzVkLTcyYmVlNmYwODhlYyIsIm9yZ2FuaXphdGlvbl9jb2RlIjoiQ29nbmljZXB0X1N5c3RlbXMiLCJhdXRob3JpemVkIjp0cnVlLCJyZWZyZXNoX2p0aSI6IjYxYjdmOGQ1LWIyMzItNGVjNy1hZWYxLTZlNGQ1OGYyYTVjZCJ9fQ.qorBAdj1-hHTVgxoWerqOFZh7fwMfh5Zg_A80cP5FVg",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2ODkyMTUyOTcsIm5iZiI6MTY4OTIxNTI5NywianRpIjoiNjFiN2Y4ZDUtYjIzMi00ZWM3LWFlZjEtNmU0ZDU4ZjJhNWNkIiwiZXhwIjoxNjkxODA3Mjk3LCJpZGVudGl0eSI6InNvbWVvbmVAZ21haWwuY29tIiwidHlwZSI6InJlZnJlc2giLCJ1c2VyX2NsYWltcyI6eyJvcmdhbml6YXRpb25faWQiOiIyZDc0N2I2My00N2U3LTQzMTYtOWM1ZC03MmJlZTZmMDg4ZWMiLCJvcmdhbml6YXRpb25fY29kZSI6IkNvZ25pY2VwdF9TeXN0ZW1zIn19.LgV8b7FJ8kbCPUpNejdJVLW__51EMPd7_Y9nygqcx9g"
}
```

You may now authorize yourself for the API calls by providing `Bearer <access_token>`
Scroll to the top of the page, click to the Authorize button. 
In the Popup value enter `Bearer <access_token>` and click Authorize
![auth](img/auth.png)

Now you are ready to call protected APIs.

#### Development
With the use of volumes/bind mounts enabled in `docker-compose.yml`, development can be done on docker as all the changes made to the code will be immediately reflected inside the container. When any other changes(.env, requirements) are made, shut down docker-compose and then run `docker-compose build` before running `docker-compose up` again

#### DB Migrations
After having made changes to the models, make a new migration for the DB with the following commands: 

`docker build -t flask_migrate_image -f Dockerfile.migrate .`

`docker run --env-file .env -v "$(pwd)":/app/ flask_migrate_image migrate -m "migration comment goes here"`

#### Run unittests
Add a nose2.cfg file on the root level to set the test path
Using Dockerfile.test build the image and run using the below commands:

`docker build -t test_image -f Dockerfile.test .`

`docker run -it --env-file .env test_image`

#### Guide to auto format python files on save
Download the VSCode Extension 'Black Formatter' 
Navigate to your VSCode settings.json file: 
- Preferences > Settings > Click on the Workspace Tab > Search for 'Editor: Code Actions On Save' 
- Click on 'Edit in settings.json'
Add the following lines to your settings.json file:
`"[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
    },
    "black-formatter.args": [
        "--skip-string-normalization",
        "--line-length=80"
    ]`
Save a python file by pressing 'ctrl s' (might be different depending on your VSCode keyboard configuration) and the formatter should automatically run  
  
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

### Release Notes
- 1.0.0 [10/12/2023]
    - Init Source Code


