from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import your OpenRouter script
import creatorStudio_openRouterVersion as studio

app = FastAPI(title="Creator Studio")

# Set up the templates directory
templates = Jinja2Templates(directory="templates")

class GenerationRequest(BaseModel):
    topic: str
    notes: str
    image_dir: str = "./creator_assets"

# Serve the web interface
# New code (fixes the error)
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# The API Endpoint the frontend will call
@app.post("/api/generate")
async def generate_studio_content(request: GenerationRequest):
    try:
        results = studio.run_pipeline(
            topic=request.topic, 
            notes=request.notes, 
            image_dir=request.image_dir
        )
        if not results:
            raise HTTPException(status_code=500, detail="Pipeline failed to generate content.")
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)