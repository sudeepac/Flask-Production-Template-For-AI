"""Tests for ML services and components.

This module contains tests for machine learning services,
model management, and ML-related functionality.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

# Import fixtures
from tests.fixtures.ml_fixtures import (
    mock_experiment_tracker,
    mock_model_registry,
    mock_sklearn_model,
    sample_model_config,
    sample_prediction_data,
    sample_training_data,
)


class TestMLModelService:
    """Test ML model service functionality."""

    def test_model_initialization(self, mock_sklearn_model):
        """Test model initialization."""
        model = mock_sklearn_model

        assert not model.is_fitted
        assert model.model_type == "classifier"
        assert model.feature_names_in_ is None

    def test_model_training(self, mock_sklearn_model, sample_training_data):
        """Test model training process."""
        model = mock_sklearn_model
        X, y = sample_training_data["X"], sample_training_data["y"]

        # Train the model
        trained_model = model.fit(X, y)

        assert trained_model.is_fitted
        assert trained_model.n_features_in_ == sample_training_data["n_features"]
        assert (
            len(trained_model.feature_names_in_) == sample_training_data["n_features"]
        )

    def test_model_prediction(
        self, mock_sklearn_model, sample_training_data, sample_prediction_data
    ):
        """Test model prediction functionality."""
        model = mock_sklearn_model
        X_train, y_train = sample_training_data["X"], sample_training_data["y"]
        X_test = sample_prediction_data["batch_samples"]

        # Train and predict
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        assert len(predictions) == len(X_test)
        assert all(pred in [0, 1] for pred in predictions)

    def test_model_prediction_probabilities(
        self, mock_sklearn_model, sample_training_data, sample_prediction_data
    ):
        """Test model probability predictions."""
        model = mock_sklearn_model
        X_train, y_train = sample_training_data["X"], sample_training_data["y"]
        X_test = sample_prediction_data["batch_samples"]

        # Train and predict probabilities
        model.fit(X_train, y_train)
        probabilities = model.predict_proba(X_test)

        assert probabilities.shape == (len(X_test), 2)
        assert np.allclose(probabilities.sum(axis=1), 1.0)
        assert np.all(probabilities >= 0) and np.all(probabilities <= 1)

    def test_model_scoring(self, mock_sklearn_model, sample_training_data):
        """Test model scoring functionality."""
        model = mock_sklearn_model
        X, y = sample_training_data["X"], sample_training_data["y"]

        # Train and score
        model.fit(X, y)
        score = model.score(X, y)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_model_parameters(self, mock_sklearn_model):
        """Test model parameter management."""
        model = mock_sklearn_model

        # Get parameters
        params = model.get_params()
        assert "model_type" in params
        assert "random_state" in params

        # Set parameters
        new_params = {"model_type": "regressor"}
        model.set_params(**new_params)
        assert model.model_type == "regressor"

    def test_unfitted_model_error(self, mock_sklearn_model, sample_prediction_data):
        """Test error handling for unfitted model."""
        model = mock_sklearn_model
        X_test = sample_prediction_data["batch_samples"]

        with pytest.raises(ValueError, match="Model is not fitted yet"):
            model.predict(X_test)

        with pytest.raises(ValueError, match="Model is not fitted yet"):
            model.predict_proba(X_test)

        with pytest.raises(ValueError, match="Model is not fitted yet"):
            model.score(X_test, [0, 1] * 5)


class TestModelRegistry:
    """Test model registry functionality."""

    def test_model_registration(self, mock_model_registry, mock_sklearn_model):
        """Test model registration."""
        registry = mock_model_registry
        model = mock_sklearn_model

        # Register model
        result = registry.register_model("test_model", model, {"version": "1.0"})

        assert result is True
        assert "test_model" in registry.models
        assert registry.metadata["test_model"]["version"] == "1.0"

    def test_model_retrieval(self, mock_model_registry, mock_sklearn_model):
        """Test model retrieval from registry."""
        registry = mock_model_registry
        model = mock_sklearn_model

        # Register and retrieve model
        registry.register_model("test_model", model)
        retrieved_model = registry.get_model("test_model")

        assert retrieved_model is model

    def test_model_listing(self, mock_model_registry, mock_sklearn_model):
        """Test listing registered models."""
        registry = mock_model_registry
        model = mock_sklearn_model

        # Register multiple models
        registry.register_model("model_1", model)
        registry.register_model("model_2", model)

        models = registry.list_models()
        assert "model_1" in models
        assert "model_2" in models
        assert len(models) == 2

    def test_model_deletion(self, mock_model_registry, mock_sklearn_model):
        """Test model deletion from registry."""
        registry = mock_model_registry
        model = mock_sklearn_model

        # Register and delete model
        registry.register_model("test_model", model)
        result = registry.delete_model("test_model")

        assert result is True
        assert "test_model" not in registry.models
        assert "test_model" not in registry.metadata

    def test_nonexistent_model_retrieval(self, mock_model_registry):
        """Test error handling for nonexistent model."""
        registry = mock_model_registry

        with pytest.raises(KeyError, match="Model 'nonexistent' not found"):
            registry.get_model("nonexistent")

    def test_metadata_management(self, mock_model_registry, mock_sklearn_model):
        """Test model metadata management."""
        registry = mock_model_registry
        model = mock_sklearn_model

        # Register model with metadata
        metadata = {"version": "1.0", "accuracy": 0.85}
        registry.register_model("test_model", model, metadata)

        # Get metadata
        retrieved_metadata = registry.get_metadata("test_model")
        assert retrieved_metadata == metadata

        # Update metadata
        new_metadata = {"accuracy": 0.90, "f1_score": 0.88}
        result = registry.update_metadata("test_model", new_metadata)

        assert result is True
        updated_metadata = registry.get_metadata("test_model")
        assert updated_metadata["version"] == "1.0"  # Original
        assert updated_metadata["accuracy"] == 0.90  # Updated
        assert updated_metadata["f1_score"] == 0.88  # New


class TestExperimentTracker:
    """Test experiment tracking functionality."""

    def test_experiment_creation(self, mock_experiment_tracker):
        """Test experiment creation."""
        tracker = mock_experiment_tracker

        experiment_id = tracker.start_experiment("test_experiment", "Test description")

        assert experiment_id is not None
        assert experiment_id.startswith("exp_")
        assert tracker.current_experiment == experiment_id

        experiment = tracker.get_experiment(experiment_id)
        assert experiment["name"] == "test_experiment"
        assert experiment["description"] == "Test description"
        assert experiment["status"] == "running"

    def test_metric_logging(self, mock_experiment_tracker):
        """Test metric logging."""
        tracker = mock_experiment_tracker

        experiment_id = tracker.start_experiment("test_experiment")

        # Log metrics
        tracker.log_metric("accuracy", 0.85, step=1)
        tracker.log_metric("accuracy", 0.87, step=2)
        tracker.log_metric("loss", 0.15, step=1)

        experiment = tracker.get_experiment(experiment_id)
        metrics = experiment["metrics"]

        assert "accuracy" in metrics
        assert "loss" in metrics
        assert len(metrics["accuracy"]) == 2
        assert metrics["accuracy"][0]["value"] == 0.85
        assert metrics["accuracy"][1]["value"] == 0.87

    def test_parameter_logging(self, mock_experiment_tracker):
        """Test parameter logging."""
        tracker = mock_experiment_tracker

        experiment_id = tracker.start_experiment("test_experiment")

        # Log parameters
        tracker.log_parameter("learning_rate", 0.01)
        tracker.log_parameter("batch_size", 32)
        tracker.log_parameter("epochs", 100)

        experiment = tracker.get_experiment(experiment_id)
        parameters = experiment["parameters"]

        assert parameters["learning_rate"] == 0.01
        assert parameters["batch_size"] == 32
        assert parameters["epochs"] == 100

    def test_artifact_logging(self, mock_experiment_tracker, temp_file):
        """Test artifact logging."""
        tracker = mock_experiment_tracker

        experiment_id = tracker.start_experiment("test_experiment")

        # Log artifact
        tracker.log_artifact(temp_file, "test_artifact")

        experiment = tracker.get_experiment(experiment_id)
        artifacts = experiment["artifacts"]

        assert "test_artifact" in artifacts
        assert artifacts["test_artifact"] == temp_file

    def test_experiment_completion(self, mock_experiment_tracker):
        """Test experiment completion."""
        tracker = mock_experiment_tracker

        experiment_id = tracker.start_experiment("test_experiment")
        tracker.end_experiment()

        experiment = tracker.get_experiment(experiment_id)
        assert experiment["status"] == "completed"
        assert tracker.current_experiment is None

    def test_multiple_experiments(self, mock_experiment_tracker):
        """Test handling multiple experiments."""
        tracker = mock_experiment_tracker

        # Create multiple experiments
        exp1 = tracker.start_experiment("experiment_1")
        tracker.end_experiment()

        exp2 = tracker.start_experiment("experiment_2")
        tracker.end_experiment()

        experiments = tracker.list_experiments()
        assert len(experiments) == 2
        assert exp1 in experiments
        assert exp2 in experiments


class TestMLDataProcessing:
    """Test ML data processing functionality."""

    def test_data_validation(self, sample_dataframe):
        """Test data validation."""
        df = sample_dataframe

        # Basic validation
        assert not df.empty
        assert len(df.columns) > 0
        assert len(df) > 0

        # Check for required columns
        required_columns = ["feature_1", "feature_2", "target"]
        for col in required_columns:
            assert col in df.columns

        # Check data types
        assert df["feature_1"].dtype in [np.float64, np.int64]
        assert df["target"].dtype in [np.int64, np.object_]

    def test_data_preprocessing(self, sample_dataframe):
        """Test data preprocessing steps."""
        df = sample_dataframe.copy()

        # Handle missing values
        initial_shape = df.shape
        df_cleaned = df.dropna()

        # Should not lose too many rows (assuming clean test data)
        assert df_cleaned.shape[0] >= initial_shape[0] * 0.9

        # Feature scaling simulation
        numerical_cols = ["feature_1", "feature_2", "feature_4"]
        for col in numerical_cols:
            # Simulate standardization
            mean_val = df[col].mean()
            std_val = df[col].std()
            df[f"{col}_scaled"] = (df[col] - mean_val) / std_val

            # Check scaling worked
            assert abs(df[f"{col}_scaled"].mean()) < 1e-10
            assert abs(df[f"{col}_scaled"].std() - 1.0) < 1e-10

    def test_feature_engineering(self, sample_dataframe):
        """Test feature engineering."""
        df = sample_dataframe.copy()

        # Create interaction features
        df["feature_1_x_feature_2"] = df["feature_1"] * df["feature_2"]

        # Create polynomial features
        df["feature_1_squared"] = df["feature_1"] ** 2

        # Create binned features
        df["feature_4_binned"] = pd.cut(
            df["feature_4"], bins=3, labels=["low", "medium", "high"]
        )

        # Validate new features
        assert "feature_1_x_feature_2" in df.columns
        assert "feature_1_squared" in df.columns
        assert "feature_4_binned" in df.columns

        # Check feature values
        assert (df["feature_1_squared"] >= 0).all()
        assert df["feature_4_binned"].isin(["low", "medium", "high"]).all()

    def test_train_test_split(self, sample_dataframe):
        """Test train-test split functionality."""
        df = sample_dataframe

        # Simulate train-test split
        train_size = int(0.8 * len(df))
        train_df = df.iloc[:train_size]
        test_df = df.iloc[train_size:]

        # Validate split
        assert len(train_df) + len(test_df) == len(df)
        assert len(train_df) > len(test_df)
        assert train_df.index.intersection(test_df.index).empty

    @pytest.mark.parametrize("test_size", [0.2, 0.3, 0.4])
    def test_different_split_ratios(self, sample_dataframe, test_size):
        """Test different train-test split ratios."""
        df = sample_dataframe

        train_size = int((1 - test_size) * len(df))
        train_df = df.iloc[:train_size]
        test_df = df.iloc[train_size:]

        actual_test_ratio = len(test_df) / len(df)
        expected_test_ratio = test_size

        # Allow for small rounding differences
        assert abs(actual_test_ratio - expected_test_ratio) < 0.05


class TestMLModelEvaluation:
    """Test ML model evaluation functionality."""

    def test_classification_metrics(self, sample_model_metrics):
        """Test classification metrics calculation."""
        metrics = sample_model_metrics["classification_metrics"]

        # Validate metric ranges
        assert 0 <= metrics["accuracy"] <= 1
        assert 0 <= metrics["precision"] <= 1
        assert 0 <= metrics["recall"] <= 1
        assert 0 <= metrics["f1_score"] <= 1
        assert 0 <= metrics["auc_roc"] <= 1

        # Validate confusion matrix
        cm = metrics["confusion_matrix"]
        assert len(cm) == 2  # Binary classification
        assert len(cm[0]) == 2
        assert all(isinstance(val, int) for row in cm for val in row)

    def test_regression_metrics(self, sample_model_metrics):
        """Test regression metrics calculation."""
        metrics = sample_model_metrics["regression_metrics"]

        # Validate metric properties
        assert metrics["mse"] >= 0
        assert metrics["rmse"] >= 0
        assert metrics["mae"] >= 0
        assert metrics["rmse"] == np.sqrt(metrics["mse"])
        assert -1 <= metrics["r2_score"] <= 1

    def test_cross_validation_simulation(
        self, mock_sklearn_model, sample_training_data
    ):
        """Test cross-validation simulation."""
        model = mock_sklearn_model
        X, y = sample_training_data["X"], sample_training_data["y"]

        # Simulate 5-fold cross-validation
        n_folds = 5
        fold_size = len(X) // n_folds
        cv_scores = []

        for i in range(n_folds):
            # Create train/validation split
            val_start = i * fold_size
            val_end = (i + 1) * fold_size if i < n_folds - 1 else len(X)

            X_val = X[val_start:val_end]
            y_val = y[val_start:val_end]
            X_train_fold = np.concatenate([X[:val_start], X[val_end:]])
            y_train_fold = np.concatenate([y[:val_start], y[val_end:]])

            # Train and evaluate
            model.fit(X_train_fold, y_train_fold)
            score = model.score(X_val, y_val)
            cv_scores.append(score)

        # Validate cross-validation results
        assert len(cv_scores) == n_folds
        assert all(0 <= score <= 1 for score in cv_scores)

        # Calculate CV statistics
        mean_score = np.mean(cv_scores)
        std_score = np.std(cv_scores)

        assert 0 <= mean_score <= 1
        assert std_score >= 0

    def test_model_comparison(self, sample_model_metrics):
        """Test model comparison functionality."""
        # Simulate multiple model results
        model_results = {
            "model_a": {"accuracy": 0.85, "f1_score": 0.83},
            "model_b": {"accuracy": 0.82, "f1_score": 0.86},
            "model_c": {"accuracy": 0.88, "f1_score": 0.85},
        }

        # Find best model by accuracy
        best_accuracy_model = max(model_results.items(), key=lambda x: x[1]["accuracy"])
        assert best_accuracy_model[0] == "model_c"

        # Find best model by F1 score
        best_f1_model = max(model_results.items(), key=lambda x: x[1]["f1_score"])
        assert best_f1_model[0] == "model_b"

        # Calculate average metrics
        avg_accuracy = np.mean(
            [metrics["accuracy"] for metrics in model_results.values()]
        )
        avg_f1 = np.mean([metrics["f1_score"] for metrics in model_results.values()])

        assert 0.8 < avg_accuracy < 0.9
        assert 0.8 < avg_f1 < 0.9


@pytest.mark.performance
class TestMLPerformance:
    """Test ML performance and scalability."""

    def test_training_performance(self, mock_sklearn_model, performance_monitor):
        """Test model training performance."""
        model = mock_sklearn_model

        # Generate larger dataset for performance testing
        np.random.seed(42)
        X_large = np.random.randn(10000, 20)
        y_large = np.random.choice([0, 1], 10000)

        # Monitor training performance
        performance_monitor.start()
        model.fit(X_large, y_large)
        stats = performance_monitor.stop()

        # Validate performance metrics
        assert stats["duration"] > 0
        assert "memory_delta" in stats
        assert "peak_memory" in stats

    def test_prediction_performance(self, mock_sklearn_model, performance_monitor):
        """Test model prediction performance."""
        model = mock_sklearn_model

        # Train model
        X_train = np.random.randn(1000, 10)
        y_train = np.random.choice([0, 1], 1000)
        model.fit(X_train, y_train)

        # Generate large prediction dataset
        X_pred = np.random.randn(50000, 10)

        # Monitor prediction performance
        performance_monitor.start()
        predictions = model.predict(X_pred)
        stats = performance_monitor.stop()

        # Validate results
        assert len(predictions) == len(X_pred)
        assert stats["duration"] > 0

        # Performance should be reasonable
        predictions_per_second = len(X_pred) / stats["duration"]
        assert predictions_per_second > 1000  # At least 1000 predictions/second

    def test_memory_usage(self, mock_sklearn_model):
        """Test memory usage during ML operations."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and train multiple models
        models = []
        for i in range(10):
            model = mock_sklearn_model
            X = np.random.randn(1000, 10)
            y = np.random.choice([0, 1], 1000)
            model.fit(X, y)
            models.append(model)

        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase > 0
        # Should not exceed 100MB for this test
        assert memory_increase < 100 * 1024 * 1024

    @pytest.mark.slow
    def test_scalability(self, mock_sklearn_model):
        """Test model scalability with different data sizes."""
        model = mock_sklearn_model

        data_sizes = [100, 1000, 10000]
        training_times = []

        for size in data_sizes:
            X = np.random.randn(size, 10)
            y = np.random.choice([0, 1], size)

            import time

            start_time = time.time()
            model.fit(X, y)
            end_time = time.time()

            training_times.append(end_time - start_time)

        # Training time should increase with data size
        # but not exponentially for this mock model
        assert training_times[1] >= training_times[0]
        assert training_times[2] >= training_times[1]

        # Time increase should be reasonable
        time_ratio = training_times[2] / training_times[0]
        assert time_ratio < 100  # Should not be more than 100x slower
