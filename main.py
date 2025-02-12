from fastapi import FastAPI,File,UploadFile,Form
import shutil
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import json
import base64

app = FastAPI()

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR,exist_ok=True)

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]
CREDS_FILE = os.getenv("GOOGLE_SERVICE_KEY","google_service_key.json")  
encoded_key = os.getenv('GOOGLE_SECRET_KEY_64')
service_account_info = json.loads(base64.b64decode(encoded_key))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = gspread.authorize(credentials)


SHEET_ID = "1Vb4EyR2nJXZqqKJG6XMaTGmLl3bCtZFAHsc8ZnALIKM"
sheet = client.open_by_key(SHEET_ID).sheet1

@app.get('/')
async def root():
    return {"Server is Running":"yes"}

@app.post('/notesupload')
async def uploadnotes(email:str=Form(...), file:UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR,f"{email}_{file.filename}")

    # saving the file
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    return {
        "message": "File uploaded successfully",
        "email": email,
        "filename": file.filename
    }

@app.post('/hackupdate')
async def hackupdates(email:str=Form(...),title:str=Form(...),venue:str=Form(...),datetime:str=Form(...),fee:str=Form(...),lastdate:str=Form(...)):

    sheet.append_row([email,title,venue,datetime,fee,lastdate])
    return {"message":"data saved successfully"}

@app.get('/gethackdetails')
async def hackdetail():
    data = sheet.get_all_values()
    data.reverse()
    print(type(data))
    return {"hackathon details":data}

