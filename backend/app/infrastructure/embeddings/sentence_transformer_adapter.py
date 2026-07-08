"""
SentenceTransformer embedding adapter implementation.
"""

from typing import cast

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.domain.interfaces.repositories import EmbeddingProvider


class SentenceTransformerAdapter(EmbeddingProvider):
    """
    Concrete adapter using local sentence-transformers models to compute vector embeddings.
    """

    def __init__(
        self,
        model_name: str | None = None,
        dimension: int | None = None,
        device: str | None = None,
    ) -> None:
        """
        Initialize the local SentenceTransformer model.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.device = device or settings.EMBEDDING_DEVICE

        # Lazy load model upon first request
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy load and cache the SentenceTransformer model.
        """
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    async def embed_query(self, text: str) -> list[float]:
        """
        Generate a unit-normalized float vector for a single query.
        """
        # Run encode synchronously as it relies on PyTorch CPU/GPU operations.
        # We cast the numpy array to list[float].
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return cast(list[float], vector.tolist())

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate unit-normalized float vectors for a list of document strings.
        """
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return cast(list[list[float]], vectors.tolist())

    def get_model_name(self) -> str:
        """
        Return the model string identifier.
        """
        return self.model_name

    def get_dimension(self) -> int:
        """
        Return the coordinate dimension length.
        """
        return self.dimension
