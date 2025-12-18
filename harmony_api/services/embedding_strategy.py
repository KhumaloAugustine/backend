"""
services/embedding_strategy.py

Embedding service using Strategy pattern for extensibility (Open/Closed Principle).
Each embedding provider is a separate, substitutable strategy.

Principles:
- Strategy Pattern: Encapsulate each embedding algorithm
- Open/Closed: Easy to add new embeddings without modifying existing code
- Dependency Inversion: Services depend on abstract strategy, not concrete implementations

Copyright (c) 2025 PAMHoYA Team
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np
import logging

from harmony_api.core.base import BaseService, ServiceError, Result

logger = logging.getLogger(__name__)


# ============================================================================
# EMBEDDING STRATEGY INTERFACE (Open/Closed Principle)
# ============================================================================

class EmbeddingStrategy(ABC):
    """
    Abstract base for embedding strategies.
    Allows adding new providers without modifying existing code.
    """
    
    @abstractmethod
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            ServiceError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and configuration."""
        pass


# ============================================================================
# CONCRETE STRATEGIES (Add new ones without modifying existing code)
# ============================================================================

class OpenAIEmbedding(EmbeddingStrategy):
    """OpenAI embedding strategy."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        Initialize OpenAI embedding.
        
        Args:
            api_key: OpenAI API key
            model: Model name
        """
        self.api_key = api_key
        self.model = model
        self.dimension = 1536
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI."""
        try:
            # Placeholder for actual OpenAI API call
            # Replace with actual openai library call
            from harmony_api.services import openai_embeddings
            
            result = openai_embeddings.generate(text, self.api_key, self.model)
            return np.array(result)
        except Exception as e:
            raise ServiceError(
                f"Failed to generate OpenAI embedding: {str(e)}",
                code="OPENAI_EMBEDDING_ERROR"
            )
    
    def get_embedding_dimension(self) -> int:
        """OpenAI ada embedding dimension."""
        return self.dimension
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get OpenAI provider info."""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "dimension": self.dimension,
            "supports_batching": True
        }


class HuggingFaceEmbedding(EmbeddingStrategy):
    """HuggingFace embedding strategy."""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize HuggingFace embedding.
        
        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name
        self._model = None
        self._dimension = None
    
    def _load_model(self):
        """Lazy load model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                # Get dimension from first encoding
                test_embedding = self._model.encode(["test"])
                self._dimension = test_embedding.shape[1]
            except Exception as e:
                raise ServiceError(
                    f"Failed to load HuggingFace model: {str(e)}",
                    code="HUGGINGFACE_MODEL_ERROR"
                )
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using HuggingFace."""
        try:
            self._load_model()
            embeddings = self._model.encode([text])
            return embeddings[0]
        except Exception as e:
            raise ServiceError(
                f"Failed to generate HuggingFace embedding: {str(e)}",
                code="HUGGINGFACE_EMBEDDING_ERROR"
            )
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get HuggingFace provider info."""
        return {
            "provider": "HuggingFace",
            "model": self.model_name,
            "dimension": self.get_embedding_dimension(),
            "supports_batching": True
        }


class AzureOpenAIEmbedding(EmbeddingStrategy):
    """Azure OpenAI embedding strategy."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_id: str,
        api_version: str = "2023-05-15"
    ):
        """
        Initialize Azure OpenAI embedding.
        
        Args:
            api_key: Azure API key
            endpoint: Azure endpoint URL
            deployment_id: Deployment ID
            api_version: API version
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_id = deployment_id
        self.api_version = api_version
        self.dimension = 1536
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Azure OpenAI."""
        try:
            # Placeholder for actual Azure OpenAI API call
            from harmony_api.services import azure_openai_embeddings
            
            result = azure_openai_embeddings.generate(
                text,
                self.api_key,
                self.endpoint,
                self.deployment_id,
                self.api_version
            )
            return np.array(result)
        except Exception as e:
            raise ServiceError(
                f"Failed to generate Azure OpenAI embedding: {str(e)}",
                code="AZURE_OPENAI_EMBEDDING_ERROR"
            )
    
    def get_embedding_dimension(self) -> int:
        """Azure OpenAI embedding dimension."""
        return self.dimension
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get Azure OpenAI provider info."""
        return {
            "provider": "Azure OpenAI",
            "endpoint": self.endpoint,
            "deployment": self.deployment_id,
            "dimension": self.dimension,
            "supports_batching": True
        }


# ============================================================================
# EMBEDDING SERVICE (Dependency Inversion)
# ============================================================================

class EmbeddingService(BaseService):
    """
    Service for generating embeddings.
    Depends on EmbeddingStrategy abstraction, not concrete implementations.
    """
    
    def __init__(self, strategy: EmbeddingStrategy):
        """
        Initialize embedding service with strategy.
        
        Args:
            strategy: Embedding strategy to use
        """
        super().__init__("EmbeddingService")
        self.strategy = strategy
        self.logger = logger
    
    def generate_embedding(self, text: str) -> Result[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Result with embedding vector
        """
        try:
            self._log_operation(
                "generate_embedding",
                "started",
                {"text_length": len(text)}
            )
            
            embedding = self.strategy.generate_embedding(text)
            
            self._log_operation(
                "generate_embedding",
                "success",
                {
                    "embedding_dim": embedding.shape[0],
                    "provider": self.strategy.get_provider_info()["provider"]
                }
            )
            
            return Result(
                data=embedding,
                metadata={
                    "provider": self.strategy.get_provider_info()["provider"],
                    "dimension": self.strategy.get_embedding_dimension()
                }
            )
        except ServiceError as e:
            self._log_operation("generate_embedding", "error", {"error": str(e)})
            return Result(error=e)
    
    def batch_generate_embeddings(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> Result[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Result with embedding matrix (n_texts x dimension)
        """
        try:
            self._log_operation(
                "batch_generate_embeddings",
                "started",
                {"num_texts": len(texts), "batch_size": batch_size}
            )
            
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = [
                    self.strategy.generate_embedding(text)
                    for text in batch
                ]
                embeddings.extend(batch_embeddings)
            
            embedding_matrix = np.array(embeddings)
            
            self._log_operation(
                "batch_generate_embeddings",
                "success",
                {
                    "num_texts": len(embeddings),
                    "matrix_shape": embedding_matrix.shape
                }
            )
            
            return Result(
                data=embedding_matrix,
                metadata={
                    "provider": self.strategy.get_provider_info()["provider"],
                    "num_embeddings": len(embeddings),
                    "matrix_shape": embedding_matrix.shape
                }
            )
        except ServiceError as e:
            self._log_operation(
                "batch_generate_embeddings",
                "error",
                {"error": str(e)}
            )
            return Result(error=e)
    
    def switch_strategy(self, new_strategy: EmbeddingStrategy) -> None:
        """
        Switch to different embedding strategy at runtime.
        
        Args:
            new_strategy: New strategy to use
        """
        old_provider = self.strategy.get_provider_info()["provider"]
        new_provider = new_strategy.get_provider_info()["provider"]
        
        self.strategy = new_strategy
        
        self._log_operation(
            "switch_strategy",
            "success",
            {
                "old_provider": old_provider,
                "new_provider": new_provider
            }
        )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get current strategy information."""
        return self.strategy.get_provider_info()


# ============================================================================
# FACTORY (Easy instantiation)
# ============================================================================

class EmbeddingServiceFactory:
    """Factory for creating embedding services."""
    
    _strategies: Dict[str, EmbeddingStrategy] = {}
    
    @classmethod
    def register_strategy(cls, name: str, strategy: EmbeddingStrategy) -> None:
        """
        Register an embedding strategy.
        
        Args:
            name: Strategy name
            strategy: Strategy instance
        """
        cls._strategies[name] = strategy
        logger.info(f"Registered embedding strategy: {name}")
    
    @classmethod
    def create(cls, strategy_name: str) -> Result[EmbeddingService]:
        """
        Create embedding service.
        
        Args:
            strategy_name: Name of registered strategy
            
        Returns:
            Result with embedding service
        """
        if strategy_name not in cls._strategies:
            return Result(
                error=ServiceError(
                    f"Unknown strategy: {strategy_name}",
                    code="UNKNOWN_STRATEGY"
                )
            )
        
        strategy = cls._strategies[strategy_name]
        service = EmbeddingService(strategy)
        return Result(data=service)


# ============================================================================
# INITIALIZATION (Self-documented setup)
# ============================================================================

def initialize_embedding_strategies(config: Dict[str, Any]) -> None:
    """
    Initialize available embedding strategies from config.
    
    Args:
        config: Configuration dictionary with provider settings
    """
    # Register OpenAI
    if "openai" in config:
        openai_config = config["openai"]
        strategy = OpenAIEmbedding(
            api_key=openai_config["api_key"],
            model=openai_config.get("model", "text-embedding-ada-002")
        )
        EmbeddingServiceFactory.register_strategy("openai", strategy)
    
    # Register HuggingFace
    if "huggingface" in config:
        hf_config = config["huggingface"]
        strategy = HuggingFaceEmbedding(
            model_name=hf_config.get("model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        )
        EmbeddingServiceFactory.register_strategy("huggingface", strategy)
    
    # Register Azure OpenAI
    if "azure" in config:
        azure_config = config["azure"]
        strategy = AzureOpenAIEmbedding(
            api_key=azure_config["api_key"],
            endpoint=azure_config["endpoint"],
            deployment_id=azure_config["deployment_id"],
            api_version=azure_config.get("api_version", "2023-05-15")
        )
        EmbeddingServiceFactory.register_strategy("azure", strategy)
