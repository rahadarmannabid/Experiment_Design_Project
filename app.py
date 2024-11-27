from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import csv
import time
import os

app = FastAPI()

# Mount static files (images for animals)
app.mount("/sequence", StaticFiles(directory="sequence"), name="sequence")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Store user data (in-memory for simplicity)
user_data = {}

# Track assignments for stratified design
age_group_assignments = {
    "Under 18": {"A": 0, "B": 0},
    "18-24": {"A": 0, "B": 0},
    "25-34": {"A": 0, "B": 0},
    "35-44": {"A": 0, "B": 0},
    "45-54": {"A": 0, "B": 0},
    "55-64": {"A": 0, "B": 0},
    "65 and over": {"A": 0, "B": 0},
}

# Model for receiving responses
class MemoryResponses(BaseModel):
    responses: list
    total_time: float  # Total time spent answering in seconds


@app.get("/", response_class=HTMLResponse)
async def demographics_form(request: Request):
    return templates.TemplateResponse("demographics.html", {"request": request})


@app.post("/submit-demographics")
async def submit_demographics(
    request: Request,
    age_range: str = Form(...),
    gender: str = Form(...),
    education: str = Form(...),
    visualization_problems: str = Form(...)
):
    # Retrieve the participant's IP address
    client_ip = request.client.host

    # Generate a unique user ID
    user_id = str(len(user_data) + 1).zfill(6)  # Ensure a 6-digit unique ID
    user_data[user_id] = {
        "age_range": age_range,
        "gender": gender,
        "education": education,
        "visualization_problems": visualization_problems,
        "ip_address": client_ip,
        "start_time": time.time(),  # Record the start time
    }

    # Determine the next version based on the stratified design
    if age_group_assignments[age_range]["A"] <= age_group_assignments[age_range]["B"]:
        version = "A"
        age_group_assignments[age_range]["A"] += 1
    else:
        version = "B"
        age_group_assignments[age_range]["B"] += 1

    # Save the version assignment in the user data
    user_data[user_id]["version"] = version

    # Check if the file exists, create it if not
    if not os.path.exists("user_data.txt"):
        with open("user_data.txt", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "user_id", "age_range", "gender", "education", "visualization_problems",
                "ip_address", "version", "responses", "total_time"
            ])

    # Append demographic data
    with open("user_data.txt", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            user_id, age_range, gender, education, visualization_problems, client_ip, version, "", ""
        ])

    # Redirect based on the assigned version
    if version == "A":
        return RedirectResponse(url=f"/version-a/{user_id}", status_code=302)
    else:
        return RedirectResponse(url=f"/version-b/{user_id}", status_code=302)


@app.get("/version-a/{user_id}", response_class=HTMLResponse)
async def version_a(request: Request, user_id: str):
    # Animal sequence
    animal_sequence = [
        "Eagle", "Cat", "Dog", "Alligator", "Deer", "Bear",
        "Cat", "Eagle", "Dog", "Deer", "Alligator", "Bear",
        "Dog", "Cat", "Eagle", "Bear", "Alligator", "Deer"
    ]
    return templates.TemplateResponse(
        "version_a.html",
        {"request": request, "user_id": user_id, "animal_sequence": animal_sequence}
    )


@app.get("/version-b/{user_id}", response_class=HTMLResponse)
async def version_b(request: Request, user_id: str):
    # Animal sequence
    animal_sequence = [
        "Eagle", "Cat", "Dog", "Alligator", "Deer", "Bear",
        "Cat", "Eagle", "Dog", "Deer", "Alligator", "Bear",
        "Dog", "Cat", "Eagle", "Bear", "Alligator", "Deer"
    ]
    return templates.TemplateResponse(
        "version_b.html",
        {"request": request, "user_id": user_id, "animal_sequence": animal_sequence}
    )



@app.get("/memory-a/{user_id}", response_class=HTMLResponse)
async def memory_a(request: Request, user_id: str):
    # Animal sequence
    animal_sequence = [
        "Eagle", "Cat", "Dog", "Alligator", "Deer", "Bear",
        "Cat", "Eagle", "Dog", "Deer", "Alligator", "Bear",
        "Dog", "Cat", "Eagle", "Bear", "Alligator", "Deer"
    ]
    return templates.TemplateResponse(
        "memory_a.html",
        {"request": request, "user_id": user_id, "animal_sequence": animal_sequence}
    )


@app.get("/memory-b/{user_id}", response_class=HTMLResponse)
async def memory_b(request: Request, user_id: str):
    # Animal sequence
    animal_sequence = [
        "Eagle", "Cat", "Dog", "Alligator", "Deer", "Bear",
        "Cat", "Eagle", "Dog", "Deer", "Alligator", "Bear",
        "Dog", "Cat", "Eagle", "Bear", "Alligator", "Deer"
    ]
    return templates.TemplateResponse(
        "memory_b.html",
        {"request": request, "user_id": user_id, "animal_sequence": animal_sequence}
    )


@app.post("/save-memory-answers/{user_id}")
async def save_memory_answers(user_id: str, memory_data: MemoryResponses):
    # Ensure total_time is calculated if not provided
    if memory_data.total_time == 0 and user_id in user_data and "start_time" in user_data[user_id]:
        memory_data.total_time = time.time() - user_data[user_id]["start_time"]

    # Read the current file contents
    rows = []
    with open("user_data.txt", "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    # Find the row corresponding to the user_id and update it
    for i, row in enumerate(rows):
        if row[0] == user_id:
            rows[i][7] = ",".join(memory_data.responses)  # Update responses
            rows[i][8] = str(memory_data.total_time)  # Update total time
            break

    # Write the updated file contents back
    with open("user_data.txt", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    # Redirect to the thank-you page after saving responses
    return RedirectResponse(url="/thanks", status_code=302)


@app.get("/thanks", response_class=HTMLResponse)
async def thanks_page(request: Request):
    return templates.TemplateResponse("thanks.html", {"request": request})
