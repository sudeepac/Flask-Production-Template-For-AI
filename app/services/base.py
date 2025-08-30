"""Base ML Service Classes.

This module contains the abstract BaseMLService class that all ML services
must inherit from. Provides consistent interface for ML model loading,
serving, caching, and lifecycle management.

See CONTRIBUTING.md §5 for ML service implementation guidelines.
"""

import abc
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from flask import current_app

from app.extensions import cache, get_logger
from app.utils.service_helpers import (
    ModelLoadError,
    PredictionError,
    handle_service_errors,
    log_service_operation,
)

logger = get_logger("app.services.base")


class BaseMLService(abc.ABC):
    """Abstract base class for all ML services.

    This class provides a consistent interface for ML model services:
    - Model loading and caching
    - Prediction serving
    - Performance monitoring
    - Error handling
    - Resource management

    All ML services MUST inherit from this class and implement
    the abstract methods.

    Example:
        class FraudDetectionService(BaseMLService):
            model_name = "fraud_detector"
            model_version = "v1.2.0"

            def _load_model(self) -> Any:
                return joblib.load(self.model_path)

            def _predict(self, model: Any, data: Dict) -> Dict:
                features = self._extract_features(data)
                prediction = model.predict_proba([features])[0]
                return {
                    "fraud_probability": float(prediction[1]),
                    "is_fraud": bool(prediction[1] > 0.5)
                }
    """

    # Subclasses must define these
    model_name: str = None
    model_version: str = None
    model_filename: str = None

    # Optional configuration
    cache_ttl: int = 3600  # Model cache TTL in seconds
    max_batch_size: int = 32
    prediction_timeout: int = 30  # Prediction timeout in seconds

    def __init__(
        self,
        model_path: Optional[str] = None,
        cache_predictions: bool = True,
        enable_monitoring: bool = True,
    ):
        """Initialize ML service.

        Args:
            model_path: Custom path to model file
            cache_predictions: Whether to cache predictions
            enable_monitoring: Whether to enable performance monitoring
        """
        if not self.model_name:
            raise ValueError("Subclasses must define 'model_name'")

        self.model_path = model_path or self._get_default_model_path()
        self.cache_predictions = cache_predictions
        self.enable_monitoring = enable_monitoring

        # Internal state
        self._model = None
        self._model_loaded_at = None
        self._model_lock = threading.RLock()
        self._prediction_count = 0
        self._total_prediction_time = 0.0
        self._error_count = 0

        # Thread pool for async predictions
        self._executor = ThreadPoolExecutor(
            max_workers=current_app.config.get("ML_MAX_WORKERS", 4),
            thread_name_prefix=f"{self.model_name}_worker",
        )

        logger.info(
            f"Initialized {self.__class__.__name__} for model '{self.model_name}'"
        )

    def _get_default_model_path(self) -> str:
        """Get default model file path.

        Returns:
            str: Path to model file
        """
        model_dir = Path(current_app.config.get("ML_MODEL_PATH", "models/"))
        filename = self.model_filename or f"{self.model_name}.pkl"
        return str(model_dir / filename)

    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded.

        Returns:
            bool: True if model is loaded
        """
        return self._model is not None

    @property
    def model_info(self) -> Dict[str, Any]:
        """Get model information and statistics.

        Returns:
            dict: Model metadata and performance stats
        """
        return {
            "name": self.model_name,
            "version": self.model_version,
            "path": self.model_path,
            "loaded": self.is_loaded,
            "loaded_at": (
                self._model_loaded_at.isoformat() if self._model_loaded_at else None
            ),
            "prediction_count": self._prediction_count,
            "error_count": self._error_count,
            "avg_prediction_time_ms": self._get_avg_prediction_time(),
            "cache_ttl": self.cache_ttl,
            "max_batch_size": self.max_batch_size,
        }

    def load_model(self, force_reload: bool = False) -> None:
        """Load ML model into memory.

        Args:
            force_reload: Force reload even if model is already loaded

        Raises:
            ModelLoadError: If model loading fails
        """
        if self.is_loaded and not force_reload:
            logger.debug(f"Model '{self.model_name}' already loaded")
            return

        with self._model_lock:
            if self.is_loaded and not force_reload:
                return  # Double-check after acquiring lock

            self._load_model_with_error_handling()

    @handle_service_errors(
        error_message="Failed to load model '{service}': {error}",
        error_type=ModelLoadError,
    )
    @log_service_operation("model_loading")
    def _load_model_with_error_handling(self) -> None:
        """Load model with centralized error handling.

        This method handles the actual model loading process with proper
        error handling and logging. It checks for file existence, loads
        the model using the subclass implementation, and validates it.

        Raises:
            ModelLoadError: If model file doesn't exist or loading fails
        """
        start_time = time.time()
        logger.info(f"Loading model '{self.model_name}' from {self.model_path}")

        # Check if model file exists
        if not Path(self.model_path).exists():
            raise ModelLoadError(f"Model file not found: {self.model_path}")

        # Load model using subclass implementation
        self._model = self._load_model()
        self._model_loaded_at = datetime.utcnow()

        load_time = time.time() - start_time
        logger.info(
            f"Model '{self.model_name}' loaded successfully in {load_time:.2f}s"
        )

        # Validate model after loading
        self._validate_model(self._model)

    def unload_model(self) -> None:
        """Unload model from memory to free resources.

        This method safely unloads the model from memory and resets
        the loading timestamp. It's thread-safe and can be called
        multiple times without issues.
        """
        with self._model_lock:
            if self._model is not None:
                logger.info(f"Unloading model '{self.model_name}'")
                self._model = None
                self._model_loaded_at = None

    @handle_service_errors(
        error_message="Prediction failed for model '{service}': {error}",
        error_type=PredictionError,
    )
    @log_service_operation("prediction", log_args=False, log_result=True)
    def predict(
        self, data: Union[Dict, List[Dict]], use_cache: bool = None
    ) -> Union[Dict, List[Dict]]:
        """Make predictions using the loaded model.

        Args:
            data: Input data for prediction (single dict or list of dicts)
            use_cache: Whether to use prediction caching (overrides instance
                setting)

        Returns:
            Prediction results (single dict or list of dicts)

        Raises:
            ModelLoadError: If model is not loaded
            PredictionError: If prediction fails
        """
        if not self.is_loaded:
            self.load_model()

        is_batch = isinstance(data, list)
        input_data = data if is_batch else [data]

        # Validate batch size
        if len(input_data) > self.max_batch_size:
            raise PredictionError(
                f"Batch size {len(input_data)} exceeds maximum {self.max_batch_size}"
            )

        # Check cache if enabled
        use_cache = use_cache if use_cache is not None else self.cache_predictions
        if use_cache:
            cached_results = self._get_cached_predictions(input_data)
            if cached_results:
                return cached_results[0] if not is_batch else cached_results

        start_time = time.time()

        # Make predictions
        with self._model_lock:
            results = []
            for item in input_data:
                result = self._predict(self._model, item)
                results.append(result)

        prediction_time = time.time() - start_time

        # Update statistics
        if self.enable_monitoring:
            self._update_prediction_stats(len(input_data), prediction_time)

        # Cache results if enabled
        if use_cache:
            self._cache_predictions(input_data, results)

        logger.debug(
            f"Predicted {len(input_data)} samples in {prediction_time:.3f}s "
            f"({prediction_time / len(input_data) * 1000:.1f}ms per sample)"
        )

        return results[0] if not is_batch else results

    def predict_async(self, data: Union[Dict, List[Dict]]) -> "Future":
        """Make asynchronous predictions.

        This method submits prediction tasks to a thread pool executor
        for non-blocking prediction processing.

        Args:
            data: Input data for prediction (single dict or list of dicts)

        Returns:
            Future: Future object for async prediction that can be awaited
        """
        return self._executor.submit(self.predict, data)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the ML service.

        Returns:
            dict: Health check results
        """
        try:
            # Check if model file exists
            model_exists = Path(self.model_path).exists()

            # Check if model is loaded
            model_loaded = self.is_loaded

            # Try to load model if not loaded
            if not model_loaded:
                try:
                    self.load_model()
                    model_loaded = True
                except Exception as e:
                    logger.warning(f"Failed to load model {self.model_name}: {e}")

            # Perform test prediction if model is loaded
            test_prediction_ok = False
            if model_loaded:
                try:
                    test_data = self._get_test_data()
                    if test_data:
                        self.predict(test_data, use_cache=False)
                        test_prediction_ok = True
                except Exception as e:
                    logger.warning(
                        f"Health check prediction failed for {self.model_name}: {e}"
                    )

            status = (
                "healthy"
                if (model_exists and model_loaded and test_prediction_ok)
                else "unhealthy"
            )

            return {
                "status": status,
                "model_exists": model_exists,
                "model_loaded": model_loaded,
                "test_prediction_ok": test_prediction_ok,
                "model_info": self.model_info,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed for {self.model_name}: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def cleanup(self) -> None:
        """Clean up resources.

        This method unloads the model and shuts down the thread pool
        executor. Should be called when the service is no longer needed
        to properly release resources.
        """
        self.unload_model()
        self._executor.shutdown(wait=True)
        logger.info(f"Cleaned up {self.__class__.__name__}")

    # Abstract methods that subclasses must implement

    @abc.abstractmethod
    def _load_model(self) -> Any:
        """Load the ML model from file.

        Returns:
            Loaded model object

        Raises:
            Exception: If model loading fails
        """

    @abc.abstractmethod
    def _predict(self, model: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single prediction using the model.

        Args:
            model: Loaded model object
            data: Input data for prediction

        Returns:
            dict: Prediction result

        Raises:
            Exception: If prediction fails
        """

    # Optional methods that subclasses can override

    def _validate_model(self, model: Any) -> None:
        """Validate the loaded model.

        This method can be overridden by subclasses to perform
        model-specific validation after loading. The default
        implementation does nothing.

        Args:
            model: Loaded model object

        Raises:
            Exception: If model validation fails
        """
        # Default implementation does nothing

    def _get_test_data(self) -> Optional[Dict[str, Any]]:
        """Get test data for health checks.

        This method can be overridden by subclasses to provide
        test data for health check predictions. The default
        implementation returns None to skip the test.

        Returns:
            dict: Test data for prediction, or None to skip test
        """
        # Default implementation returns None (skip test)
        return None

    # Private helper methods

    def _get_cached_predictions(self, data: List[Dict]) -> Optional[List[Dict]]:
        """Get cached predictions if available.

        This method attempts to retrieve cached prediction results
        for the given input data. If any item in the batch is not
        cached, returns None to indicate a cache miss.

        Args:
            data: List of input data dictionaries

        Returns:
            List of cached prediction results, or None if cache miss
        """
        if not cache:
            return None

        try:
            cache_keys = [self._get_cache_key(item) for item in data]
            cached_results = []

            for key in cache_keys:
                result = cache.get(key)
                if result is None:
                    return None  # Cache miss for any item means no cache
                cached_results.append(result)

            logger.debug(f"Cache hit for {len(data)} predictions")
            return cached_results

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
            return None

    def _cache_predictions(self, data: List[Dict], results: List[Dict]) -> None:
        """Cache prediction results.

        This method stores prediction results in the cache for future
        retrieval. Each input-result pair is cached with a generated
        cache key and the configured TTL.

        Args:
            data: List of input data dictionaries
            results: List of corresponding prediction results
        """
        if not cache:
            return

        try:
            for item, result in zip(data, results):
                cache_key = self._get_cache_key(item)
                cache.set(cache_key, result, timeout=self.cache_ttl)

            logger.debug(f"Cached {len(results)} predictions")

        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")

    def _get_cache_key(self, data: Dict) -> str:
        """Generate cache key for input data.

        Creates a deterministic cache key by hashing the input data.
        The key includes the model name and version to ensure cache
        isolation between different models.

        Args:
            data: Input data dictionary

        Returns:
            str: Generated cache key
        """
        import hashlib
        import json

        # Create deterministic hash of input data
        data_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        return f"ml_prediction:{self.model_name}:{self.model_version}:{data_hash}"

    def _update_prediction_stats(self, count: int, time_taken: float) -> None:
        """Update prediction statistics.

        This method updates internal counters for monitoring
        prediction performance and usage.

        Args:
            count: Number of predictions made
            time_taken: Total time taken for predictions in seconds
        """
        self._prediction_count += count
        self._total_prediction_time += time_taken

    def _get_avg_prediction_time(self) -> float:
        """Get average prediction time in milliseconds.

        Calculates the average time per prediction based on
        accumulated statistics.

        Returns:
            float: Average prediction time in milliseconds, or 0.0 if no predictions made
        """
        if self._prediction_count == 0:
            return 0.0
        return (self._total_prediction_time / self._prediction_count) * 1000
