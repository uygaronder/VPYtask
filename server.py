# Description: A simple FastAPI server that accepts a CSV file as input and returns a JSON response. The server also makes 
#   a request to an external API and combines the data from both sources.
# usage example: uvicorn server:app --reload

from fastapi import FastAPI, File, UploadFile
import csv
import requests

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Authenticate and obtain access token
url = "https://api.baubuddy.de/index.php/login"
payload = {
    "username": "365",
    "password": "1"
}
headers = {
    "Authorization": "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
    "Content-Type": "application/json"
}
response = requests.request("POST", url, json=payload, headers=headers)
access_token = response.json()["oauth"]["access_token"]

## temp read csv
import csv

with open('vehicles.csv', newline='') as csvfile:
    csv_data = csvfile.read()
    vehicles = {'file': ('vehicles.csv', csv_data)}
## temp read csv

@app.post("/vehicles")
async def create_vehicle(file: UploadFile = File(...)):
    contents = await file.read()
    decoded = contents.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded)
    vehicles = []
    for row in reader:
        vehicles.append(row)

    #Request the resources located at https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get("https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active", headers=headers)
    api_data = response.json()

    # Storing api response
    data = []
    for vehicle in vehicles:
        if vehicle not in data:
            data.append(vehicle)
    for api_vehicle in api_data:
        if api_vehicle not in data:
            data.append(api_vehicle)
            
    # Filtering out any resources without a value set for hu field
    data = [vehicle for vehicle in data if vehicle.get("hu")]

    # For each labelId in the vehicle's JSON array labelIds resolve its colorCode using https://api.baubuddy.de/dev/index.php/v1/labels/{labelId}
    for vehicle in data:
        label_colors = []
        label_ids = vehicle.get("labelIds")
        
        if label_ids is not None and isinstance(label_ids, list):
            for label_id in label_ids:
                headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                label_response = requests.get(f"https://api.baubuddy.de/dev/index.php/v1/labels/{label_id}", headers=headers)
                label_data = label_response.json()
                label_colors.append(label_data.get("colorCode"))
        
        vehicle["labelColors"] = label_colors

    # Return data-structure in JSON format
    return {"data": data}