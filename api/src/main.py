import os
import numpy as np
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel, ConfigDict, Field
from typing import List

from starlette.requests import Request
from starlette.responses import Response

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from fastapi.responses import RedirectResponse


from redis import asyncio as aioredis

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import T5Tokenizer, TFT5ForConditionalGeneration


app = FastAPI()

app.mount("/static/", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NeuralSearcher:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        # Initialize encoder model
        self.model = SentenceTransformer("all-mpnet-base-v2", device="cpu")
        # initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url="https://2d07b4a8-24db-4676-abb6-418f473ac9d1.us-east4-0.gcp.cloud.qdrant.io:6333",
            api_key="6OTjaLmZvTrP5F4kds0_nm2IxvbevsiBfL9jAPHByE8TPgBQ8jaTjg",
        )

    def search(self, text: str):
        # Convert text query into vector
        vector = self.model.encode(text).tolist()

        # Use `vector` for search for closest vectors in the collection
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=None,  # We don't want any filters for now
            limit=10,  # 5 the most closest results is enough
        )
        # `search_result` contains found vector ids with similarity scores along with the stored payload
        # In this function we are interested in payload only

        payloads_with_scores = [
            {
                "answer": hit.payload[
                    "answer"
                ],  # Assuming each hit has a payload with an "answer" key
                "score": hit.score,
            }
            for hit in search_result
        ]
        return payloads_with_scores
    
    def RAG_search(self, text: str):
        #importing the model - Flan-T5 base
        t5_model = TFT5ForConditionalGeneration.from_pretrained('google/flan-t5-base')
        t5_tokenizer = T5Tokenizer.from_pretrained('google/flan-t5-base')

        #creating the context
        hits = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=self.model.encode(text).tolist(),
            query_filter=None,
            limit=10,)
        context = ""
        for hit in hits:
            context += hit.payload['sentence'] + ". "
        #using FLAN-T5 + adding the context
        
        t5_context_text = context
        t5_question_text = text
        t5_qa_input_text = 'Answer the question: ' + t5_question_text + '?' + t5_context_text
        t5_inputs = t5_tokenizer([t5_qa_input_text], truncation = True, return_tensors='tf')
        t5_summary_ids = t5_model.generate(t5_inputs['input_ids'])
        prediction = [t5_tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in t5_summary_ids]
        prediction = str(prediction[0])
        return prediction


# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name="tw_test")
encoder = SentenceTransformer("all-mpnet-base-v2")


async def startup_event():
    global model
    # model = load("model_pipeline.pkl")  # Load model

    # Set up the Redis cache backend
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = os.environ.get("REDIS_PORT", 6379)
    redis_url = f"redis://{redis_host}:{redis_port}"
    redis = await aioredis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


app.router.add_event_handler("startup", startup_event)



@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api")
def search_startup(q: str):
    search_results = neural_searcher.search(q)
    return {"results": search_results}


@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/static/index.html")


# @app.post("/submit_question")
# async def submit_question(question_text: str):
#     # Add your logic here to process the question (e.g., store in a database, send to another service, etc.)
#     # For simplicity, we'll just print the question text to the console
#     search_results = neural_searcher.search(question_text)
#     complete_answer = "What is " + search_results[0]["answer"] + "?"
#     return {"answer": complete_answer} 

@app.post("/submit_question")
async def submit_question(question_text: str):
    # Add your logic here to process the question (e.g., store in a database, send to another service, etc.)
    # For simplicity, we'll just print the question text to the console
    search_results = neural_searcher.RAG_search(question_text)
    complete_answer = "What is " + search_results + "?"
    return {"answer": complete_answer} 