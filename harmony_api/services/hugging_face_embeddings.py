import numpy as np
from sentence_transformers import SentenceTransformer

from harmony_api.constants import HUGGINGFACE_MINILM_L12_V2, HUGGINGFACE_MPNET_BASE_V2, \
    HUGGINGFACE_MENTAL_HEALTH_HARMONISATION_1, LABSE_MODEL

# Load Hugging Face sentence transformers
print("INFO:\t  Checking Hugging Face models...")
model_huggingface_minilm_l12_v2 = SentenceTransformer(
    HUGGINGFACE_MINILM_L12_V2["model"]
)
model_huggingface_mpnet_base_v2 = SentenceTransformer(
    HUGGINGFACE_MPNET_BASE_V2["model"]
)
model_huggingface_mental_health_harmonisation = SentenceTransformer(
    HUGGINGFACE_MENTAL_HEALTH_HARMONISATION_1["model"]
)
# Load LaBSE for South African languages
print("INFO:\t  Loading LaBSE model for South African languages...")
try:
    model_labse = SentenceTransformer(LABSE_MODEL["model"])
    print("INFO:\t  LaBSE model loaded successfully")
except Exception as e:
    print(f"WARNING:\t  Could not load LaBSE model: {str(e)}")
    model_labse = None

def __get_hugging_face_embeddings(texts: list[str], model_name: str) -> np.ndarray:
    """
    :param texts: List of texts.
    :param model_name: The model name.

    Get Hugging Face embeddings.
    """

    if not texts:
        return np.array([])

    embeddings = []

    if model_name == HUGGINGFACE_MINILM_L12_V2["model"]:
        embeddings = model_huggingface_minilm_l12_v2.encode(
            sentences=texts, convert_to_numpy=True
        )
    elif model_name == HUGGINGFACE_MPNET_BASE_V2["model"]:
        embeddings = model_huggingface_mpnet_base_v2.encode(
            sentences=texts, convert_to_numpy=True
        )
    elif model_name == HUGGINGFACE_MENTAL_HEALTH_HARMONISATION_1["model"]:
        embeddings = model_huggingface_mental_health_harmonisation.encode(
            sentences=texts, convert_to_numpy=True
        )
    elif model_name == LABSE_MODEL["model"]:
        if model_labse is not None:
            embeddings = model_labse.encode(
                sentences=texts, 
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for better multilingual matching
            )
        else:
            return np.array([])

    return embeddings


def get_hugging_face_embeddings_mpnet_base_v2(texts: list[str]) -> np.ndarray:
    """
    :param texts: List of texts.

    Get Hugging Face embeddings.
    """

    return __get_hugging_face_embeddings(
        texts=texts, model_name=HUGGINGFACE_MPNET_BASE_V2["model"]
    )


def get_hugging_face_embeddings_minilm_l12_v2(texts: list[str]) -> np.ndarray:
    """
    :param texts: List of texts.

    Get Hugging Face embeddings.
    """

    return __get_hugging_face_embeddings(
        texts=texts, model_name=HUGGINGFACE_MINILM_L12_V2["model"]
    )


def get_hugging_face_embeddings_harmonydata_mental_health_harmonisation_1(texts: list[str]) -> np.ndarray:
    """
    :param texts: List of texts.

    Get Hugging Face embeddings.
    """

    return __get_hugging_face_embeddings(
        texts=texts, model_name=HUGGINGFACE_MENTAL_HEALTH_HARMONISATION_1["model"]
    )


def get_labse_embeddings(texts: list[str]) -> np.ndarray:
    """
    Get LaBSE embeddings optimized for South African languages.
    
    LaBSE supports 109 languages including:
    - Zulu (zu)
    - Xhosa (xh)
    - Sotho (st)
    - Afrikaans (af)
    - And 105 other languages
    
    :param texts: List of texts to embed.
    :return: Array of embeddings with L2 normalization for better multilingual matching.
    """
    return __get_hugging_face_embeddings(
        texts=texts, model_name=LABSE_MODEL["model"]
    )
