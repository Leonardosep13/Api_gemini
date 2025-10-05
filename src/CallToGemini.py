from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import fitz
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SoulStation API", description="API for SoulStation", version="alpha")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    raise RuntimeError("The environment variable GENAI_API_KEY must be set.")

genai.configure(api_key=api_key)

document_content = ""

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str

class DiagnoseRequest(BaseModel):
    temperature: float
    fat_porcent: float
    weight: float
    height: float
    age: int
    mood: str
    cough: bool
    other_symptoms: str
    

# Función para extraer texto de un PDF usando PyMuPDF
def extract_with_pymupdf(path):
    parts = []
    doc = fitz.open(path)
    for page in doc:
        text = page.get_text("text")
        if text:
            parts.append(text)
    doc.close()
    return "\n".join(parts)

@app.on_event("startup")
async def startup_event():
    global document_content
    pdf_filename = "./data/Dataset_Soulstation.pdf"
    try:
        document_content = extract_with_pymupdf(pdf_filename)
        print(f"Document loaded successfully. Content length: {len(document_content)} characters")
    except Exception as e:
        print(f"Error loading document: {e}")

@app.post("/diagnose")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if not document_content:
        raise HTTPException(status_code=500, detail="Document not loaded")
    
    try:
        prompt = f"""
You are an expert assistant whose only knowledge comes from the documents provided.
You must respond exclusively based on the information contained in those documents or contextual excerpts.
If the information is missing or insufficient, reply with a phrase such as:

"I don't have enough information in the documents to answer that question."

You should also keep in mind that the questions come from an astronaut on a space mission, so try to sound friendly, approachable, and understanding.
Avoid being too technical or complicated—use simple and clear language. Do not mention that the information comes from a document, as that would sound robotic and distant.

Do not make up data, do not assume, and do not include any external information.
Keep your answers clear, concise, and faithful to the original content.
You must respond in the same language in which you are asked.
Avoid giving too much information—only provide what is necessary for the astronaut to understand the answer with just the right amount of words.
Text:
---
{document_content}
---

Question: {request.question}
"""
        
        model = genai.GenerativeModel('gemini-pro-latest')
        response = model.generate_content(prompt)
        
        return QuestionResponse(answer=response.text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.get("/")
async def root():
    return {"message": "The api is working"}