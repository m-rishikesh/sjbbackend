from fastapi import FastAPI,File,UploadFile,Form,HTTPException
import shutil
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
origins = [
    "http://localhost:5173", 
    "https://sjbconnect.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR,exist_ok=True)

#Google_Drive
creds = ServiceAccountCredentials.from_json_keyfile_name('google_service_key.json', ['https://www.googleapis.com/auth/drive.file'])

drive_service = build('drive', 'v3', credentials=creds)





#Google_Sheet Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "google_service_key.json"  

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(credentials)


hackdetail_sheet_id = "1Vb4EyR2nJXZqqKJG6XMaTGmLl3bCtZFAHsc8ZnALIKM" #hackdata_sheet_id
notesdata_sheet_id = "1UnH_hlT6vOG-mFvA9iJjbStUsa-2UqW-GlOEHM-w434" #notesdata_sheet_id
sheet = client.open_by_key(hackdetail_sheet_id).sheet1
notesheets = client.open_by_key(notesdata_sheet_id).sheet1


@app.get('/')
async def root():
    return {"Server is Running":"yes"}

@app.post('/notesupload')
async def uploadnotes(email:str=Form(...),subject:str=Form(...),branch:str=Form(...),year:str=Form(...), file:UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR,f"{email}_{file.filename}")

    # saving the file
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    #uploading the file to google drive
    file_metadata = {'name':file.filename, 'mimeType': file.content_type}
    media = MediaFileUpload(file_path,mimetype=file.content_type)

    drive_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    permission = {
        'type': 'anyone',  # Set the type to "anyone" to make it public
        'role': 'reader'  # Grant read permission
    }

    drive_service.permissions().create(
        fileId=drive_file['id'],
        body=permission
    ).execute()

    public_url_file = f"https://drive.google.com/file/d/{drive_file['id']}/view"

    os.remove(file_path)
    isAvailable = False
    notesheets.append_row([email,public_url_file,drive_file['id'],year,branch,subject,isAvailable])

    return {
        "message": "File uploaded successfully",
        "email": email,
        "filename": file.filename,
        "file_url": f"https://drive.google.com/file/d/{drive_file['id']}/view",
    }

@app.post('/hackupdate')
async def hackupdates(email:str=Form(...),title:str=Form(...),venue:str=Form(...),datetime:str=Form(...),fee:str=Form(...),lastdate:str=Form(...)):
    isAvailable = False
    sheet.append_row([email,title,venue,datetime,fee,lastdate,isAvailable])
    print(email)
    print(datetime)
    print(venue)
    print(title)
    print(lastdate)
    
    return {"message":"data saved successfully",}

@app.get('/gethackdetails')
async def hackdetail():
    hackdetail = []
    data = sheet.get_all_values()

    is_available_index = data[0].index('isAvailable')
    for i,record in enumerate(data[1:],start=2):
        if record[is_available_index] == 'TRUE':
            hackdetail.append(record)
    hackdetail.reverse()
    return hackdetail


def deletenotes(file_id):
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return {f"Deleted Successfully"}
    except HttpError as err:
        raise HTTPException(status_code=400, detail=f"Error deleting file: {err}")
    
@app.delete('/deletenotes/{email}')
async def deletenote(email:str):
    row_list = []
    file_id_list = []
    try:
        records = notesheets.get_all_records()
        for i,record in enumerate(records,start=2):
            if record['email'] == email:
                row_list.append(i)
                file_id_list.append(record.get('notesid'))
        
        if not row_list:
            raise HTTPException(status_code=404, detail=f"Email {email} not found in the sheet.")
        
        user_row_deleted = row_list[-1]
        last_id_deleted = file_id_list[-1]

        deletenotes(last_id_deleted)

        notesheets.delete_rows(user_row_deleted)

        return {f"notes deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting row: {e}")


@app.get('/getnotes')
async def getnotesapi():
    notes_from_g_sheet = notesheets.get_all_records()
    notes_array_of_objects = []

    for record in notes_from_g_sheet: 
     dictionary = {
        'subject': record.get('subject'),  
        'year': record.get('year'),
        'branch': record.get('branch'),
        'noteslink': record.get('noteslink'),
        'isAvailable': record.get('isAvailable')
    }
     if(dictionary['isAvailable']=='TRUE'):
        notes_array_of_objects.append(dictionary)

    return notes_array_of_objects

    
