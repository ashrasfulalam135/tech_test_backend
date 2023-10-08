from fastapi.testclient import TestClient
from app.main import app
import hashlib

client = TestClient(app)

# valid input data
valid_input = {
    "input_query": "SELECT name, age FROM employee where department = 'PD' AND working_year > 3"
}
valid_map = {
    "name": hashlib.sha256('name'.encode()).hexdigest(),
    "age": hashlib.sha256('age'.encode()).hexdigest(),
    "department": hashlib.sha256('department'.encode()).hexdigest(),
    "working_year": hashlib.sha256('working_year'.encode()).hexdigest()
}
valid_output = {
    "input_query": valid_input['input_query'],
    "modified_query": f"SELECT {valid_map['name']}, {valid_map['age']} FROM employee where {valid_map['department']} = 'PD' AND {valid_map['working_year']} > 3",
    "hashed_column_map": valid_map
}

# invalid input data
invalid_input = {
    "input_query": "SELECT name, age FROM where department = 'PD' AND working_year > 3" #table name not exists
}
invalid_output = {
    "input_query": invalid_input['input_query'],
    "message": "Invalid Query"
}

def test_parse_sql_for_valid_query():
    response = client.post("/", json=valid_input)
    assert response.status_code == 200
    assert response.json() == valid_output
    
def test_parse_sql_for_invalid_query():
    response = client.post("/", json=invalid_input)
    assert response.status_code == 200
    assert response.json() == invalid_output