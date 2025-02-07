import time
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


class PineconeVectorStore:
    def __init__(self, index_name="final-similarity-1", dimension=1536, metric="cosine", cloud="aws",
                 region="us-east-1"):
        # Load environment variables
        load_dotenv()

        # Fetch API key from environment variables
        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is not set in environment variables.")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.cloud = cloud
        self.region = region

        # Setup index
        self._setup_index()

        # Initialize the Pinecone Vector Store
        self.pinecone_index = self.pc.Index(self.index_name)

    def _setup_index(self):
        existing_indexes = [index_info["name"] for index_info in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(cloud=self.cloud, region=self.region),
            )
            while not self.pc.describe_index(self.index_name).status["ready"]:
                time.sleep(1)

    def query(self, vector, filters=None, k=5):
        """
        Queries the Pinecone index for similar vectors.

        Parameters:
            vector (list): The embedding vector to search.
            filters (dict, optional): Metadata filters for query.
            k (int, optional): Number of top results to fetch.

        Returns:
            dict: Query results.
        """
        return self.pinecone_index.query(
            vector=vector,
            top_k=k,
            include_values=True,
            include_metadata=True,
            filter=filters
        )

