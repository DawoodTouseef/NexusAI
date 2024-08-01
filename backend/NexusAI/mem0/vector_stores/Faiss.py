import os
import shutil
import logging
from typing import Optional, List, Any, Dict

import faiss
import numpy as np
from pydantic import BaseModel, Field
from mem0.vector_stores.base import VectorStoreBase


class FAISS(VectorStoreBase, BaseModel):
    index: Optional[faiss.Index] = None
    index_file: str = Field(default="faiss.index")
    dimension: int = Field(default=128)  # Example dimension, adjust as needed
    logger: logging.Logger = Field(default=logging.getLogger(__name__))
    collections: Dict[str, faiss.Index] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.logger.info(f"Initializing FAISS index with dimension: {self.dimension}")
        if os.path.exists(self.index_file):
            self.logger.info(f"Loading FAISS index from file: {self.index_file}")
            self.index = faiss.read_index(self.index_file)
        else:
            self.logger.info(f"Creating a new FAISS index with dimension: {self.dimension}")
            self.index = faiss.IndexFlatL2(self.dimension)

    def create_col(self, name: str, vector_size: int, distance: str):
        self.logger.info(f"Creating a new collection: {name} with vector size: {vector_size} and distance: {distance}")
        if name in self.collections:
            raise ValueError(f"Collection {name} already exists")
        if distance == "l2":
            self.collections[name] = faiss.IndexFlatL2(vector_size)
        elif distance == "ip":
            self.collections[name] = faiss.IndexFlatIP(vector_size)
        else:
            raise ValueError(f"Unsupported distance type: {distance}")

    def insert(self, name: str, vectors: List[List[float]], payloads: Optional[List[Any]] = None, ids: Optional[List[int]] = None):
        self.logger.info(f"Inserting vectors into collection: {name}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        collection = self.collections[name]
        vectors_array = np.array(vectors, dtype=np.float32)
        if ids:
            ids_array = np.array(ids, dtype=np.int64)
            collection.add_with_ids(vectors_array, ids_array)
        else:
            collection.add(vectors_array)

    def search(self, name: str, query: List[float], limit: int = 5, filters: Optional[Dict] = None) -> List[int]:
        self.logger.info(f"Searching in collection: {name} with limit: {limit}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        collection = self.collections[name]
        query_array = np.array([query], dtype=np.float32)
        distances, indices = collection.search(query_array, limit)
        return indices[0].tolist()

    def delete(self, name: str, vector_id: int):
        self.logger.info(f"Deleting vector with ID: {vector_id} from collection: {name}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        # FAISS does not support direct deletion of vectors, typically we need to rebuild the index without the deleted vector

    def update(self, name: str, vector_id: int, vector: Optional[List[float]] = None, payload: Optional[Any] = None):
        self.logger.info(f"Updating vector with ID: {vector_id} in collection: {name}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        # Updating is similar to deletion; FAISS typically requires rebuilding the index

    def get(self, name: str, vector_id: int):
        self.logger.info(f"Retrieving vector with ID: {vector_id} from collection: {name}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        # FAISS does not support direct retrieval of vectors by ID

    def list_cols(self) -> List[str]:
        self.logger.info("Listing all collections")
        return list(self.collections.keys())

    def delete_col(self, name: str):
        self.logger.info(f"Deleting collection: {name}")
        if name in self.collections:
            del self.collections[name]
        if os.path.exists(f"{name}.index"):
            os.remove(f"{name}.index")

    def col_info(self, name: str):
        self.logger.info(f"Getting information about collection: {name}")
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        collection = self.collections[name]
        return {
            "ntotal": collection.ntotal,
            "d": collection.d
        }

    def save_index(self):
        self.logger.info(f"Saving FAISS index to file: {self.index_file}")
        if not self.index:
            raise ValueError("Index not initialized")
        faiss.write_index(self.index, self.index_file)

    def clear_index(self):
        self.logger.info(f"Clearing the FAISS index and removing the file: {self.index_file}")
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        self.index = faiss.IndexFlatL2(self.dimension)

    def delete_index(self):
        self.logger.info(f"Deleting the FAISS index and the index file: {self.index_file}")
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        self.index = None

# Example usage:
faiss_store = FAISS(dimension=128)
faiss_store.create_col('my_collection', 128, 'l2')
faiss_store.insert('my_collection', [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]])
indices = faiss_store.search('my_collection', [0.1, 0.2, 0.3, 0.4])
print(indices)
