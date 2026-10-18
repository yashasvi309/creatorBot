from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Import your local Ollama + Gemma 4 script
# (Make sure your Ollama pipeline file is named `creator_studio_ollama.py`)
import creator_studio_ollama as studio

app = FastAPI(title="Open-Source Creator Studio (Local Ollama + Gemma 4)")

# Set up the templates directory (ensure index.html is inside ./templates)
templates = Jinja2Templates(directory="templates")


class GenerationRequest(BaseModel):
    topic: str
    notes: str
    image_dir: str = "./creator_assets"


# Ensure dummy assets exist on server startup
@app.on_event("startup")
async def startup_event():
    studio.setup_dummy_assets("./creator_assets")


# Serve the web interface
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# The API Endpoint the frontend will call
@app.post("/api/generate")
def generate_studio_content(request: GenerationRequest):
    """
    Runs the 3-agent local Ollama + Gemma 4 pipeline synchronously in FastAPI's
    threadpool so blocking `requests` and `time.sleep` calls don't freeze the event loop.
    """
    try:
        # 1. Verify Ollama is reachable before running the pipeline
        if not studio.validate_environment():
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Cannot connect to local Ollama server at {studio.OLLAMA_BASE_URL}. "
                    f"Ensure `ollama serve` is running and `{studio.MODEL_NAME}` is pulled."
                ),
            )

        # 2. Ensure the requested asset directory has fallback images if newly created
        studio.setup_dummy_assets(request.image_dir)

        # 3. Run the 3-Agent Pipeline
        results = studio.run_pipeline(
            topic=request.topic,
            notes=request.notes,
            image_dir=request.image_dir,
        )

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Local Ollama pipeline failed to generate content.",
            )

        return {"status": "success", "data": results}

    except HTTPException:
        raise
    except SystemExit:
        # Catch sys.exit(1) from run_pipeline() so FastAPI doesn't crash
        raise HTTPException(
            status_code=503,
            detail="Local Ollama validation failed. Make sure Ollama is running (`ollama serve`).",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)