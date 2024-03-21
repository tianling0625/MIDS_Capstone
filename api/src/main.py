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
        self.model = SentenceTransformer('all-mpnet-base-v2', device='cpu')
        # initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url="https://2d07b4a8-24db-4676-abb6-418f473ac9d1.us-east4-0.gcp.cloud.qdrant.io:6333",
            api_key="6OTjaLmZvTrP5F4kds0_nm2IxvbevsiBfL9jAPHByE8TPgBQ8jaTjg")
        
    def search(self, text: str):
        # Convert text query into vector
        vector = self.model.encode(text).tolist()

        # Use `vector` for search for closest vectors in the collection
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=None,  # We don't want any filters for now
            limit=3  # 5 the most closest results is enough
        )
        # `search_result` contains found vector ids with similarity scores along with the stored payload
        # In this function we are interested in payload only

        payloads_with_scores = [{
            "answer": hit.payload["answer"],  # Assuming each hit has a payload with an "answer" key
            "score": hit.score  
            } for hit in search_result]
        return payloads_with_scores
    
# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='tw_test')
encoder = SentenceTransformer("all-mpnet-base-v2")


async def startup_event():
    global model
    # model = load("model_pipeline.pkl")  # Load model

    # Set up the Redis cache backend
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    redis_url = f"redis://{redis_host}:{redis_port}"
    redis = await aioredis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

app.router.add_event_handler("startup", startup_event)


# # Use pydantic.Extra.forbid to only except exact field set from client.
# # This was not required by the lab.
# # Your test should handle the equivalent whenever extra fields are sent.
# class House(BaseModel):
#     """Data model to parse the request body JSON."""

#     model_config = ConfigDict(extra="forbid")

#     MedInc: float = Field(gt=0)
#     HouseAge: float
#     AveRooms: float
#     AveBedrms: float
#     Population: float
#     AveOccup: float
#     Latitude: float
#     Longitude: float

#     def to_np(self):
#         return np.array(list(vars(self).values())).reshape(1, 8)


# class HousePrediction(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     prediction: float

# # New BulkHouseRequest for accepting a list of House inputs
# class BulkHouse(BaseModel):
#     houses: List[House]
#     def to_np(self):
#         return np.array([house.to_np().flatten() for house in self.houses])

# # New response model for bulk predictions
# class BulkHousePrediction(BaseModel):
#     predictions: List[float]

# @app.post("/predict", response_model=HousePrediction)
# # @cache(expire=60)  # Cache for 60 seconds
# async def predict(house: House):
#     prediction = model.predict(house.to_np())[0]
#     return {"prediction": prediction}


# # New endpoint for bulk predictions
# @app.post("/bulk_predict", response_model=BulkHousePrediction)
# @cache(expire=60)  # Cache for 60 seconds
# async def bulk_predict(houses: BulkHouse):
#     predictions = model.predict(houses.to_np())
#     return {"predictions": predictions.tolist()}
#     # return BulkHousePrediction(predictions=predictions.tolist())


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api")
def search_startup(q: str):
    search_results = neural_searcher.search(q)
    return {
        "results": search_results
    }

@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/static/index.html")

# #Endpoints for index.html with template rendering
# @app.get("/", response_class=HTMLResponse)
# async def read_item(request: Request):
#     return templates.TemplateResponse("index2.html", {"request": request})


# Define a simple endpoint to handle questions
@app.post("/submit_question")
async def submit_question(question_text: str):
    # Add your logic here to process the question (e.g., store in a database, send to another service, etc.)
    # For simplicity, we'll just print the question text to the console
    search_results = neural_searcher.search(question_text)
    return {"answer": search_results[0]["answer"]}