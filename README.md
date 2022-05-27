# fastapi-course
sample code from fastapi-course learning

# Fastapi 

### Purpose

Python api development

[YouTube course](https://www.youtube.com/watch?v=0sOvCWFmrtA&ab_channel=freeCodeCamp.org)

### Prepare

```shell
python3 -m venv venv
source venv/bin/activate
pip install "fastapi[all]"
```

## Start Server

```shell
# reload only in develop mode.
uvicorn main:app --reload 
# api docs could be found at localhost:8000/docs
```

## Schema

```python
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastApi()

class PostCreate(BaseModel):
  title: str
  content: str

class Post(PostCreate):
  published: bool
 
@app.post("/posts")
def create_post(post: PostCreate):
  print(post)
  print(post.dict())
  return {"data": post}

@app.get("/posts", response_model=List[Post])
def get_post():
  posts = [{"title":"first", "content":"f", "published": "True"}]
  return posts
  
```

## postgres

 **install pyscopg2**

`pip install psycopg2-binary`

**Usage**

```python
conn = psycopg2.connect("dbname=fastapi user=postgres password=xxxx")
cursor = conn.cursor()

# create
cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *;""", 
        (post.title, post.content, post.published)) 
new_post = cursor.fetchone()
conn.commit()

# get
cursor.execute("SELECT * FROM posts WHERE id = %s;", (id,))
post = cursor.fetchone()

# delete
cursor.execute("DELETE FROM posts WHERE id = %s RETURNING *;", (id,))
deleted_post = cursor.fetchone()
conn.commit()

#update
cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s  WHERE id = %s RETURNING *""",
         (post.title, post.content, post.published, id))
post = cursor.fetchone()
conn.commit()
```

Command line

```shell
su - postgres
psql -u postgres
postgres=#
postgres=# \password postgres
postgres=# \q
```



## Routers

Spilt router into different module.

Routers.post.py

```python
from fastapi import Response, status, HTTPException, APIRouter
from fastapi.params import Depends

from sqlalchemy.orm.session import Session

from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get("/", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)): 
    posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    return posts

```

Routers.user.py

```python
from typing import List
from fastapi import Response, status, HTTPException, APIRouter
from fastapi.params import Depends

from sqlalchemy.orm.session import Session

from .. import models, schemas, utils
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail=f"user with id {id} does not exists")
    return user
```

Main.py

```python
from fastapi import FastAPI

from . import models
from .database import engine
from .routers import post, user

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(post.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "hello world"}
```



## Sqlalchemy 

-- database orm

**Usage**:

### database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:xxxxx@localhost/fastapi"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### main.py

```python
from typing import List
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Depends
from . import models, schemas
from .database import engine, get_db
        
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/posts", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return posts

# add return constraint
@app.get("/posts/{id}",  response_model=schemas.Post)
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"post with id: {id} does not exist")
    return post

@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not found")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}",  response_model=PostCreated)
def update_post(id: int, updated_post:schemas.PostCreate, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id) 
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not found")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()
  

```

### schema.py

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class PostBase(BaseModel):
    title: str
    content: str 
    published: bool = True

class PostCreate(PostBase):
    pass

class UserOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Post(PostBase):
    id: int 
    created_at: datetime
    owner_id: int 
    owner: UserOut
    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str 


class TokenData(BaseModel):
    id: Optional[str] = None 
```

### models.py

```python
from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, text
from sqlalchemy.orm import relationship
from .database import Base

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False) 
    published = Column(Boolean, server_default='TRUE')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
     owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User")

    def __str__(self) -> str:
        return f"id {self.id} title {self.title} content {self.content}"
```

## PasswordHash

`pip install "passlib[bcrypt]"`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)
```

## JWT(JSON Web Token)

What is the JSON Web Token structure?

In its compact form, JSON Web Tokens consist of three parts separated by dots (`.`), which are:

- Header
- Payload
- Signature

Therefore, a JWT typically looks like the following.

```xml
xxxxx.yyyyy.zzzzz
```

Signature

`HMACSHA256(base64UrlEncode(header) + "." +  base64UrlEncode(payload),  secret)`

Where secret should only keep privately on server side.

**Usage**

`pip install "python-jose[cryptography]"`

**oauth2.py**

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import schemas, database, models

oauth2_schema = OAuth2PasswordBearer(tokenUrl='login')

#SECRET_KEY
#Algorithm
#Expriation time

SECRET_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_access_token(token:str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception
    
    return token_data


def get_current_user(token: str = Depends(oauth2_schema), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})

    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token.id).first() 
    return user
```

In routers.py

```python
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)
```

## Environment variables

First, create a setting class, map the variables in env automatically.

```python
# config.py
from pydantic import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_password: str
    database_port: str
    database_name: str
    database_username: str
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"


settings = Settings()
```

Then, create a file name ".env" (Just in development. In Production, set these settings as env variables), remember not to upload this file into your git repository.

```python
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=xxxxxxxx
DATABASE_NAME=fastapi
DATABASE_USERNAME=postgres
SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

Finally, replace all reference data to settings.xxx

## Alembic

Database migrations allow us to incrementally track changes to database schema and rollback changes to any point in time.

Alembic can also automatically pull database models from Sqlalchemy and generate the proper tables

```shell
# install 
pip install alembic
# init, second alembic would be the directory we need.
alembic init alembic
```



Preparation

```python
# env.py
from app.models import Base 
# remeber import from model so that models would be created automatically.
from app.config import settings
config = context.config
# this will replace sqlalchemy.url in alembic.ini
config.set_main_option(
    "sqlalchemy.url", 
    f"postgresql+psycopg2://{settings.database_username}:{settings.database_password}@{settings.database_hostname}/{settings.database_name}")
```

Usage

```shell
alembic --help
alembic revision -m "create post table"
alembic upgrade [+1|head|xxxx]
alembic downgrade -2
alembic downgrade yyyyyyy
alembic history

# change models such as add a column, and then
alembic revision --autogenerate -m "create posts users and votes" 
alembic upgrade head
```

## Heroku

deploy our app in heorku.

1. register a account at heroku
2. seach for "heroku python", and in setup menu, download the app, install it.
3. in command shell: `heroku login -i `
4. After logon, create remote repository by: heroku create unique-app-name
5. upload your code: `git push heroku main `
6. create a "Procfile" in our project root 



create a postgres in heroku

1. create postgres:  `heroku addons:create heroku-postgresql:hobby-dev`
2. add env variables on heroku.com, select data. on datastores>settings>show Database Credentials; click our app, then in "Config Vars" area, just add the args we need.
3. restart the app: `heroku ps:restart`
4. Create database: `heroku run "alembic upgrade head"`



## Ubuntu

1. apply for a remote ubuntu server on cloud server provider, such as digitalocean
2. Logon the ubuntu server with ssh: `ssh root@ipaddr`
3. upgrade ubuntu library: `sudo apt update && sudo apt upgrade -y`
4. install python-pip `sudo apt install python3-pip`
5. install vritualenv `sudo pip3 install virtualenv`
6. install postgres `sudo apt install postgresql postgresql-contrib -y`
7. Create user: `adduser newuser`
8. Grant root access for new user `usermod -aG sudo newuser`
9. upload product code to server。 `mkdir src && cd src && git clone xxx.git .`
10. create virtual env `virtualenv venv`
11. Active venv `source venv\bin\activate`
12. setting env vironment: `cd ~ && touch .env`
13. .env file are just key=value pairs, without export before every line.
14. `set -o allexport; source ~/.env; set +o allexport`
15. `printenv` all key=value pairs in .env will be add to environments
16. Add command in 14 to .profile, then reboot will still contains all env variables.
17. `pip instal gunicorn  uvloop httptools`
18. restart our server automatically when reboot with: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000`



create our app server: 

```shell
cd /etc/systemd/system
sudo vi api.service

# template 
[Unit]
Description=demo fastapi application
After=network.target

[Service]
User=sanjeev
Group=sanjeev
WorkingDirectory=/home/sanjeev/app/src/
Environment="PATH=/home/sanjeev/app/venv/bin"
EnvironmentFile=/home/sanjeev/.env
ExecStart=/home/sanjeev/app/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target

# :wq
# sudo systemctl enable api
# systemctl status api
```

## NGINX

- High performance webserver that can act as a proxy

- Can handle SSL termination

  ```shell
  sudo apt install nginx -y
  systemctl start nginx
  cd /etc/nginx/sites-available && sudo vi default
  
  ################3
  server {
          listen 80 default_server;
          listen [::]:80 default_server;
  
          server_name _; # replace with specific domain name like sanjeev.com
          
          location / {
                  proxy_pass http://localhost:8000;    ### our gunicorn
                  proxy_http_version 1.1;
                  proxy_set_header X-Real-IP $remote_addr;
                  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                  proxy_set_header Upgrade $http_upgrade;
                  proxy_set_header Connection 'upgrade';
                  proxy_set_header Host $http_host;
                  proxy_set_header X-NginX-Proxy true;
                  proxy_redirect off;
          }
  }
  # :wq
  ```

get a domain name, (namecheap\GoDaddy) for https purpose

use Certbot to create certificate (https)



Configure firewall:

```shell
sudo utw status
sudo ufw allow http
sudo utw allow https
sudo utw allow ssh
sudo ufw enable
```



Dockerfile

`docker build -t fastapi .`

`docker image ls`



Docker-composer.yml

create a account in docker hub.

`docker-compose up -d`  rebuild image

`docker ps -a` list all docker images

`docker logs container_name` see logs in container.

`docker-compose down`



docker login

docker push image-name



pytest

`pip install pytest`

## Github pipeline(CI/CD)

https://github.com/marketplace search for useful action

Example code .github/workflows/build-deploy.yml

```yaml
name: Build and Deploy Code

on: [push, pull_request]

jobs:
  build: 
    environment: 
      name: testing
    env:
      DATABASE_HOSTNAME: ${{secrets.DATABASE_HOSTNAME}}
      DATABASE_PORT: ${{secrets.DATABASE_PORT}}
      DATABASE_PASSWORD: ${{secrets.DATABASE_PASSWORD}} 
      DATABASE_NAME: ${{secrets.DATABASE_NAME}}
      DATABASE_USERNAME: ${{secrets.DATABASE_USERNAME}}
      SECRET_KEY: ${{secrets.SECRET_KEY}}
      ALGORITHM: ${{secrets.ALGORITHM}}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${{secrets.ACCESS_TOKEN_EXPIRE_MINUTES}}
    services:
      # Label used to access the service container
      postgres:
        # Docker Hub image
        image: postgres
        # Provide the password for postgres
        env:
          POSTGRES_PASSWORD: ${{secrets.DATABASE_PASSWORD}} 
          POSTGRES_DB: ${{secrets.DATABASE_NAME}}_test
        ports:
          - 5432:5432 
        # Set health checks to wait until postgres has started
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    runs-on: ubuntu-latest
    steps:
      - name: pulling git repo
        uses: actions/checkout@v2
      - name: Install -python version 3.9
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - name: update pip
        run: python -m pip install --upgrade pip
      - name: install all dependencies
        run: pip install -r requirements.txt
      - name: test with pytest
        run: |
          pip install pytest
          pytest
      
      # - name: Login to Docker Hub
      #   uses: docker/login-action@v1
      #   with:
      #     username: ${{ secrets.DOCKER_HUB_USERNAME }}
      #     password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}

      # - name: Set up Docker Buildx
      #   uses: docker/setup-buildx-action@v1

      # - name: Build and push
      #   uses: docker/build-push-action@v2
      #   with:
      #     context: ./
      #     file: ./Dockerfile
      #     builder: ${{ steps.buildx.outputs.name }}
      #     push: true
      #     tags: ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi:latest
      #     cache-from: type=registry,ref=${{ secrets.DOCKER_HUB_USERNAME }}/fastapi:buildcache
      #     cache-to: type=registry,ref=${{ secrets.DOCKER_HUB_USERNAME }}/fastapi:buildcache,mode=max

  deploy:
    runs-on: ubuntu-latest
    needs: [build]
    environment:
      name: production

    steps:
      - name: pulling git repo
        uses: actions/checkout@v2
      - name: deploying to heroku
        uses: akhileshns/heroku-deploy@v3.12.12 # This is the action
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: ${{secrets.HEROKU_APPNAME}} #Must be unique in Heroku
          heroku_email: ${{secrets.HEROKU_EMAIL}}
      
      # pull our github repo
      # install heroku cli
      # heroku login
      # add git remote for heroku
      # git push heroku main

      # - name: deploy to ubuntu server
      #   uses: appleboy/ssh-action@master
      #   with:
      #     host: ${{secrtes.PROD_HOST}}
      #     username: ${{secrets.PROD_USERNAME}}
      #     password: ${{serects.PROD_PASSWORD}}
      #     script: |
      #       cd app/src
      #       git pull
      #       echo  ${{serects.PROD_PASSWORD}} | sudo -S systemctl restart api 

```

Remember to create env variables in your github account. 

## Pytest

`pip install pytest`

 conftest.py

```python
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.main import app

from app.config import settings
from app.database import get_db
from app.database import Base
from app.oauth2 import create_access_token
from app import models
from alembic import command


# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password123@localhost:5432/fastapi_test'
SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test'


engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    print("my session fixture ran")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():

        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user2(client):
    user_data = {"email": "sanjeev123@gmail.com",
                 "password": "password123"}
    res = client.post("/users/", json=user_data)

    assert res.status_code == 201

    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture
def test_user(client):
    user_data = {"email": "sanjeev@gmail.com",
                 "password": "password123"}
    res = client.post("/users/", json=user_data)

    assert res.status_code == 201

    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})


@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }

    return client


@pytest.fixture
def test_posts(test_user, session, test_user2):
    posts_data = [{
        "title": "first title",
        "content": "first content",
        "owner_id": test_user['id']
    }, {
        "title": "2nd title",
        "content": "2nd content",
        "owner_id": test_user['id']
    },
        {
        "title": "3rd title",
        "content": "3rd content",
        "owner_id": test_user['id']
    }, {
        "title": "3rd title",
        "content": "3rd content",
        "owner_id": test_user2['id']
    }]

    def create_post_model(post):
        return models.Post(**post)

    post_map = map(create_post_model, posts_data)
    posts = list(post_map)

    session.add_all(posts)
    # session.add_all([models.Post(title="first title", content="first content", owner_id=test_user['id']),
    #                 models.Post(title="2nd title", content="2nd content", owner_id=test_user['id']), models.Post(title="3rd title", content="3rd content", owner_id=test_user['id'])])
    session.commit()

    posts = session.query(models.Post).all()
    return posts

```

test_post.py

```python
import pytest
from app import schemas


def test_get_all_posts(authorized_client, test_posts):
    res = authorized_client.get("/posts/")

    def validate(post):
        return schemas.PostOut(**post)
    posts_map = map(validate, res.json())
    posts_list = list(posts_map)

    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200


def test_unauthorized_user_get_all_posts(client, test_posts):
    res = client.get("/posts/")
    assert res.status_code == 401


def test_unauthorized_user_get_one_post(client, test_posts):
    res = client.get(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_get_one_post_not_exist(authorized_client, test_posts):
    res = authorized_client.get(f"/posts/88888")
    assert res.status_code == 404


def test_get_one_post(authorized_client, test_posts):
    res = authorized_client.get(f"/posts/{test_posts[0].id}")
    post = schemas.PostOut(**res.json())
    assert post.Post.id == test_posts[0].id
    assert post.Post.content == test_posts[0].content
    assert post.Post.title == test_posts[0].title


@pytest.mark.parametrize("title, content, published", [
    ("awesome new title", "awesome new content", True),
    ("favorite pizza", "i love pepperoni", False),
    ("tallest skyscrapers", "wahoo", True),
])
def test_create_post(authorized_client, test_user, test_posts, title, content, published):
    res = authorized_client.post(
        "/posts/", json={"title": title, "content": content, "published": published})

    created_post = schemas.Post(**res.json())
    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.content == content
    assert created_post.published == published
    assert created_post.owner_id == test_user['id']


def test_create_post_default_published_true(authorized_client, test_user, test_posts):
    res = authorized_client.post(
        "/posts/", json={"title": "arbitrary title", "content": "aasdfjasdf"})

    created_post = schemas.Post(**res.json())
    assert res.status_code == 201
    assert created_post.title == "arbitrary title"
    assert created_post.content == "aasdfjasdf"
    assert created_post.published == True
    assert created_post.owner_id == test_user['id']


def test_unauthorized_user_create_post(client, test_user, test_posts):
    res = client.post(
        "/posts/", json={"title": "arbitrary title", "content": "aasdfjasdf"})
    assert res.status_code == 401


def test_unauthorized_user_delete_Post(client, test_user, test_posts):
    res = client.delete(
        f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_delete_post_success(authorized_client, test_user, test_posts):
    res = authorized_client.delete(
        f"/posts/{test_posts[0].id}")

    assert res.status_code == 204


def test_delete_post_non_exist(authorized_client, test_user, test_posts):
    res = authorized_client.delete(
        f"/posts/8000000")

    assert res.status_code == 404


def test_delete_other_user_post(authorized_client, test_user, test_posts):
    res = authorized_client.delete(
        f"/posts/{test_posts[3].id}")
    assert res.status_code == 403


def test_update_post(authorized_client, test_user, test_posts):
    data = {
        "title": "updated title",
        "content": "updatd content",
        "id": test_posts[0].id

    }
    res = authorized_client.put(f"/posts/{test_posts[0].id}", json=data)
    updated_post = schemas.Post(**res.json())
    assert res.status_code == 200
    assert updated_post.title == data['title']
    assert updated_post.content == data['content']


def test_update_other_user_post(authorized_client, test_user, test_user2, test_posts):
    data = {
        "title": "updated title",
        "content": "updatd content",
        "id": test_posts[3].id

    }
    res = authorized_client.put(f"/posts/{test_posts[3].id}", json=data)
    assert res.status_code == 403


def test_unauthorized_user_update_post(client, test_user, test_posts):
    res = client.put(
        f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_update_post_non_exist(authorized_client, test_user, test_posts):
    data = {
        "title": "updated title",
        "content": "updatd content",
        "id": test_posts[3].id

    }
    res = authorized_client.put(
        f"/posts/8000000", json=data)

    assert res.status_code == 404

```

running test: `pytest`



## Utility

Postman : help to develop api faster. Environment variables, Bearer token setting.

**Git**: 

1. add ssh-key into your GitHub account
2. create a repository
3. git clone git@xxx.git

**Chrome**

F12->console->send request to test CROS

`fetch('http://localhost:8000/').then(res=>res.json()).then(console.log)`

**Pip**

pip freeze > requirements.txt 

pip install -r requirements.txt

## Reference

[fastapi](https://fastapi.tiangolo.com/zh/)

[Psycopg3](https://www.psycopg.org/psycopg3/docs/basic/install.html)

[heroku-dev](https://devcenter.heroku.com/articles/getting-started-with-python#deploy-the-app)

[heroku postgres](https://devcenter.heroku.com/articles/heroku-postgresql)

[docker hub](https://hub.docker.com/)