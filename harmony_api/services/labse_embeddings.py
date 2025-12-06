"""
LaBSE (Language-agnostic BERT Sentence Embeddings) embeddings service
for South African language support including Zulu, Xhosa, Sotho, and other African languages.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from harmony_api.constants import LABSE_MODEL

# Load LaBSE model for South African languages
print("INFO:\t  Loading LaBSE model for South African languages...")
try:
    model_labse = SentenceTransformer(LABSE_MODEL["model"])
    print("INFO:\t  LaBSE model loaded successfully")
except Exception as e:
    print(f"WARNING:\t  Could not load LaBSE model: {str(e)}")
    model_labse = None


def __get_labse_embeddings(texts: list[str]) -> np.ndarray:
    """
    Get LaBSE embeddings for texts.
    LaBSE supports 109 languages including South African languages.
    
    Parameters
    ----------
    texts : list[str]
        List of texts to embed.
    
    Returns
    -------
    np.ndarray
        Array of embeddings with shape (len(texts), embedding_dim).
    """
    if not texts or model_labse is None:
        return np.array([])
    
    try:
        embeddings = model_labse.encode(
            sentences=texts,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for better cosine similarity
        )
        return embeddings
    except Exception as e:
        print(f"ERROR:\t  Could not generate LaBSE embeddings: {str(e)}")
        return np.array([])


def get_labse_embeddings(texts: list[str]) -> np.ndarray:
    """
    Get LaBSE embeddings for input texts.
    Optimized for South African languages (Zulu, Xhosa, Sotho, etc.).
    
    Parameters
    ----------
    texts : list[str]
        List of texts to embed.
    
    Returns
    -------
    np.ndarray
        Array of embeddings.
    """
    return __get_labse_embeddings(texts=texts)
