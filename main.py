from fastapi import FastAPI, UploadFile, File, Form
import whisper
import shutil
import os
import subprocess
import requests

app = FastAPI()
print("🔄 Đang load Whisper model...")
model = whisper.load_model("base")
print("✅ Whisper model đã sẵn sàng!")

def convert_to_wav(input_path, output_path):
    print(f"🎧 Chuyển {input_path} → {output_path} (wav)...")
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path, output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ Convert xong.")

def call_gentle(audio_path: str, transcript: str):
    print(f"📡 Gửi dữ liệu vào Gentle server...")
    try:
        with open(audio_path, 'rb') as audio_file:
            response = requests.post(
                "http://localhost:8765/transcriptions?async=false",
                files={
                    "audio": audio_file,
                    "transcript": (None, transcript)
                },
                timeout=20  # tránh bị treo
            )
        print(f"✅ Nhận phản hồi từ Gentle ({response.status_code})")
        return response.json()
    except Exception as e:
        print("❌ Lỗi khi gọi Gentle:", e)
        return {"words": []}

def compare_score(user_words: list, target_words: list):
    correct = sum(1 for u, t in zip(user_words, target_words) if u.lower() == t.lower())
    return round(correct / len(target_words) * 100, 2) if target_words else 0

@app.post("/evaluate-speaking")
async def evaluate_speaking(file: UploadFile = File(...), target_text: str = Form(...)):
    print("📥 Nhận file:", file.filename)
    input_m4a = "temp.m4a"
    temp_wav = "temp.wav"

    # Save file
    try:
        with open(input_m4a, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print("✅ Đã lưu file m4a tạm.")
    except Exception as e:
        print("❌ Lỗi khi lưu file:", e)
        return {"error": "Could not save audio file."}

    # Convert to wav
    convert_to_wav(input_m4a, temp_wav)

    # Whisper transcript
    print("🧠 Đang chạy Whisper...")
    result = model.transcribe(temp_wav)
    user_text = result.get("text", "").strip()
    print("📝 Whisper transcript:", user_text)

    # Nếu voice rỗng hoặc không có từ nào
    if not user_text:
        print("⚠️ Transcript rỗng – không gọi Gentle.")
        try:
            os.remove(input_m4a)
            os.remove(temp_wav)
        except:
            pass
        return {
            "user_text": "",
            "score": 0,
            "alignment": [],
            "error": "Whisper không nghe thấy gì trong voice bạn gửi."
        }

    # Call Gentle
    gentle_result = call_gentle(temp_wav, user_text)
    if "words" not in gentle_result:
        print("⚠️ Không có 'words' trong gentle_result")
        return {"error": "Gentle failed hoặc trả về không hợp lệ."}

    # Extract words for scoring
    user_words = [w["alignedWord"] for w in gentle_result["words"] if w["case"] == "success"]
    target_words = target_text.strip().split()
    print("📊 user_words:", user_words)
    print("🎯 target_words:", target_words)

    score = compare_score(user_words, target_words)
    print(f"🏁 Score: {score}%")

    # Clean up
    try:
        os.remove(input_m4a)
        os.remove(temp_wav)
        print("🧹 Đã xoá file tạm.")
    except:
        pass

    return {
        "user_text": user_text,
        "score": score,
        "alignment": gentle_result["words"]
    }
