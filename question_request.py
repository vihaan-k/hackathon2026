from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Define the structure of the JSON data you expect
class QuestionPayload(BaseModel):
    question: str

@app.post("/process")
async def process_question(payload: QuestionPayload):
    # Extract the string directly from the parsed payload
    question_string = payload.question
    
    # Use the Python string in your functions
    print("Received string:", question_string)
    
    return {"status": "success", "received": question_string}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)