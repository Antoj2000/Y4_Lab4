import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, get_db
from app.models import Base
# if pytest is not working
# change directory : cd "C:\Users\johns\OneDrive - Atlantic TU\CICD3\Labs\Lab2\Y4_Lab2"
# run python -m pytest


# USE STATIC POOL TO FIX
TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # hand the client to the test
        yield c
        # --- teardown happens when the 'with' block exits ---

def user_payload(student_id="S1234567", name= "Anthony", email= "user@example.com", age=24):
    return {
        "student_id": student_id,
        "name": name,
        "email": email,
        "age": age
    }

def project_payload(name="Test Project", description="A test project", owner_id=1):
    return {
        "name": name,
        "description": description,
        "owner_id": owner_id
    }

# ------- User Tests -------

# Create user successfully
def test_create_user(client):
    r = client.post("/api/users", json=user_payload()) 
    assert r.status_code == 201

 # Create user dupe   
def test_create_user_conflict(client):
    r = client.post("/api/users", json=user_payload()) # try to create same user again
    assert r.json()["detail"] == "User already exists"

# will repeat test with bad student ids
@pytest.mark.parametrize("bad_sid", ["S1234", "1234567", "S12345678", "s1234567", "S1234A67"])
def test_bad_student_id(client, bad_sid):
    r = client.post("/api/users", json=user_payload(email="aj@gmail.com", student_id=bad_sid)) 
    assert r.status_code == 422


def test_delete_then_404(client):
    r = client.post("/api/users", json=user_payload(student_id="S6666666", email="deleteme@yahoo.com")) # create user 
    r = client.delete("/api/users/delete/2") # delete user
    assert r.status_code == 204
    r = client.get("/api/users/2") # try to get deleted user
    assert r.status_code == 404  

def test_update_user(client):
    r = client.post("/api/users", json=user_payload(student_id="S7654321", email="update@bing.com")) # create user 
    r = client.put("/api/users/update/2", json=user_payload(student_id="S8654321",email="update@bing.com", name="Conor")) # update user name + ID
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Conor"
    r = client.get("/api/users/2") # get updated user
    data = r.json()
    assert data["name"] == "Conor"

def test_patch_user(client):
    r = client.post("/api/users", json=user_payload(student_id="S0000002", email="patch@bing.com")) # create user 
    r = client.patch("/api/users/patch/3", json={"name": "Conor"}) # update user name + ID
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Conor"
    r = client.get("/api/users/3") # get updated user
    data = r.json()
    assert data["name"] == "Conor"


def test_update_account_404(client):
    r = client.put("/api/users/update/4", json=user_payload()) # update non-existent user
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found" 

# ------ Project Tests -------

# Create project suscessfully
def test_create_project(client):
    r = client.post("/api/projects", json=project_payload()) 
    assert r.status_code == 201

# Create project with bad user
def test_create_project_bad_user(client):
    r = client.post("/api/projects", json=project_payload(owner_id=666)) # no valid user
    assert r.json()["detail"] == "User not found"

def test_update_project(client):
    r = client.post("/api/projects", json=project_payload(name="UpdateProject")) # create Project
    r = client.put("/api/projects/update/2", json=project_payload(name="UpdatedProject")) # update project name
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "UpdatedProject"
    r = client.get("/api/projects/2") # get updated user
    data = r.json()
    assert data["name"] == "UpdatedProject"

def test_patch_project(client):
    r = client.post("/api/projects", json=project_payload(name="PatchProject")) # create Project
    r = client.patch("/api/projects/patch/3", json={"name": "PatchedProject"}) # update project name
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "PatchedProject"
    r = client.get("/api/projects/3") # get updated user
    data = r.json()
    assert data["name"] == "PatchedProject"
                  