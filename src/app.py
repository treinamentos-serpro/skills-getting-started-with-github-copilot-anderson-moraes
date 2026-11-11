"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

current_dir = Path(__file__).parent
static_source_dir = current_dir / "static"
static_build_dir = current_dir.parent / "dist"
static_dir = static_build_dir if static_build_dir.is_dir() else static_source_dir
app.mount("/static", StaticFiles(directory=static_dir), name="static")

UPLOAD_DIR = current_dir / "uploads"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.post("/files", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    filename = Path((file.filename or "").replace("\\", "/")).name
    if filename in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="A valid filename is required")

    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit")

    file_id = str(uuid4())
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / file_id).write_bytes(contents)
    (UPLOAD_DIR / f"{file_id}.json").write_text(
        json.dumps({"filename": filename}), encoding="utf-8"
    )
    return {"id": file_id, "filename": filename, "size": len(contents)}


@app.get("/files")
def list_files():
    files = []
    if not UPLOAD_DIR.is_dir():
        return {"files": files}

    for metadata_path in UPLOAD_DIR.glob("*.json"):
        try:
            file_id = str(UUID(metadata_path.stem))
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            file_path = UPLOAD_DIR / file_id
            if file_path.is_file():
                files.append({
                    "id": file_id,
                    "filename": metadata["filename"],
                    "size": file_path.stat().st_size,
                })
        except (OSError, ValueError, KeyError, TypeError):
            continue

    files.sort(key=lambda item: item["filename"].casefold())
    return {"files": files}


@app.get("/files/{file_id}")
def download_file(file_id: str):
    try:
        file_id = str(UUID(file_id))
        metadata = json.loads(
            (UPLOAD_DIR / f"{file_id}.json").read_text(encoding="utf-8")
        )
        file_path = UPLOAD_DIR / file_id
        if not file_path.is_file():
            raise FileNotFoundError
    except (ValueError, OSError, KeyError, TypeError):
        raise HTTPException(status_code=404, detail="File not found") from None

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=metadata["filename"],
    )
