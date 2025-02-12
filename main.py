from fastapi import FastAPI,File,UploadFile,Form
import shutil
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR,exist_ok=True)

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "google_service_key.json"  

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
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

