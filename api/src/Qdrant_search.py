from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class NeuralSearcher:

    def __init__(self, collection_name):
        self.collection_name = collection_name
        # Initialize encoder model
        self.model = SentenceTransformer('all-mpnet-base-v2', device='cpu')
        # initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url="https://2d07b4a8-24db-4676-abb6-418f473ac9d1.us-east4-0.gcp.cloud.qdrant.io:6333",
            api_key="6OTjaLmZvTrP5F4kds0_nm2IxvbevsiBfL9jAPHByE8TPgBQ8jaTjg")