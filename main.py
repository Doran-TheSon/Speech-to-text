from fastapi import FastAPI, UploadFile, File
import whisper
import shutil
import os

app = FastAPI()
model = whisper.load_model("base")  # Các option: tiny, base, small, medium, large

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_file = "temp_audio.m4a"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = model.transcribe(temp_file)
    os.remove(temp_file)
    return {"text": result["text"]}
