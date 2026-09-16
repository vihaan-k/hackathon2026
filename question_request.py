from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (great for local testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

class QuestionPayload(BaseModel):
    question: str

@app.post("/process")
async def process_question(payload: QuestionPayload):
    question_string = payload.question
    print("Received string:", question_string)
    return {"status": "success", "received": question_string}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)