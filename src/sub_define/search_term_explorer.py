import requests
import os
import zipfile
from io import BytesIO
from scipy import spatial
import numpy as np


class NewSearchTermExplorer:
    """Ingest GLoVe vectors and explore new search terms.

    This gets called if user specifies in the main script.
    """

    def __init__(
        self,
        sample_terms: str,
        vector_url: str,
        unzip_path: str,
    ):
        self.sample_terms = sample_terms
        self.vector_url = vector_url
        self.unzip_path = unzip_path

        # conduct ingestion immediately
        glove_zip_url = self.vector_url
        glove_zip_response = requests.get(glove_zip_url)
        glove_zip = zipfile.ZipFile(BytesIO(glove_zip_response.content))
        unzip_path = self.unzip_path
        glove_zip.extractall(unzip_path)
        del glove_zip_response, glove_zip
        glove_vector_path = unzip_path + os.listdir(unzip_path)[0]

        # load glove vectors & find search terms
        embeddings_dict = {}
        with open(glove_vector_path, "r") as f:
            for line in f:
                values = line.split(" ")
                word = values[0]
                vector = np.asarray(values[1:], dtype="float32")
                embeddings_dict[word] = vector

        self.embeddings_dict = embeddings_dict

    def find_closest_embeddings(self, embedding):
        """Find closest embeddings to a given embedding."""
        embeddings_dict = self.embeddings_dict

        return sorted(
            embeddings_dict.keys(),
            key=lambda word: spatial.distance.euclidean(
                embeddings_dict[word], embedding
            ),
        )

    def explore(self):
        """Explore closest embeddings for user-specified sample terms."""
        search_terms = self.sample_terms
        embeddings_dict = self.embeddings_dict
        for term in search_terms:
            try:
                closest_embeddings = self.find_closest_embeddings(
                    embeddings_dict[term]
                )[1:11]
                print(f"Closest terms to {term}:")
                print(closest_embeddings)
            except KeyError:
                pass  # term not in embeddings

        os.remove(self.unzip_path + os.listdir(self.unzip_path)[0])
        os.rmdir(self.unzip_path)
