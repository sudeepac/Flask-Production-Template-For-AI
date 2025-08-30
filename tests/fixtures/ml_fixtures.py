"""Machine Learning test fixtures.

This module contains fixtures specifically for testing
machine learning components and services.
"""

import os

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="function")
def sample_training_data():
    """Sample training data for ML models."""
    np.random.seed(42)  # For reproducible results

    # Generate synthetic dataset
    n_samples = 1000
    n_features = 5

    X = np.random.randn(n_samples, n_features)
    # Create target with some correlation to features
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1 > 0).astype(int)

    feature_names = [f"feature_{i}" for i in range(n_features)]

    return {
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "n_samples": n_samples,
        "n_features": n_features,
    }


@pytest.fixture(scope="function")
def sample_prediction_data():
    """Sample data for making predictions."""
    np.random.seed(123)

    return {
        "single_sample": np.random.randn(5),
        "batch_samples": np.random.randn(10, 5),
        "feature_names": [f"feature_{i}" for i in range(5)],
    }


@pytest.fixture(scope="function")
def sample_dataframe():
    """Sample pandas DataFrame for testing."""
    np.random.seed(42)

    data = {
        "id": range(1, 101),
        "feature_1": np.random.randn(100),
        "feature_2": np.random.randn(100),
        "feature_3": np.random.choice(["A", "B", "C"], 100),
        "feature_4": np.random.uniform(0, 100, 100),
        "target": np.random.choice([0, 1], 100),
    }

    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def mock_sklearn_model():
    """Mock scikit-learn model for testing."""

    class MockSklearnModel:
        def __init__(self, model_type="classifier"):
            self.model_type = model_type
            self.is_fitted = False
            self.feature_names_in_ = None
            self.n_features_in_ = None
            self.classes_ = np.array([0, 1]) if model_type == "classifier" else None

        def fit(self, X, y=None):
            self.is_fitted = True
            self.n_features_in_ = X.shape[1] if hasattr(X, "shape") else len(X[0])
            self.feature_names_in_ = [
                f"feature_{i}" for i in range(self.n_features_in_)
            ]
            return self

        def predict(self, X):
            if not self.is_fitted:
                raise ValueError("Model is not fitted yet.")

            n_samples = X.shape[0] if hasattr(X, "shape") else len(X)

            if self.model_type == "classifier":
                return np.random.choice([0, 1], n_samples)
            else:  # regressor
                return np.random.randn(n_samples)

        def predict_proba(self, X):
            if self.model_type != "classifier":
                raise AttributeError("Regressor doesn't have predict_proba method")

            if not self.is_fitted:
                raise ValueError("Model is not fitted yet.")

            n_samples = X.shape[0] if hasattr(X, "shape") else len(X)
            proba = np.random.rand(n_samples, 2)
            # Normalize to sum to 1
            proba = proba / proba.sum(axis=1, keepdims=True)
            return proba

        def score(self, X, y):
            if not self.is_fitted:
                raise ValueError("Model is not fitted yet.")
            return np.random.uniform(0.7, 0.95)

        def get_params(self, deep=True):
            return {"model_type": self.model_type, "random_state": 42}

        def set_params(self, **params):
            for key, value in params.items():
                setattr(self, key, value)
            return self

    return MockSklearnModel()


@pytest.fixture(scope="function")
def mock_model_registry():
    """Mock model registry for testing."""

    class MockModelRegistry:
        def __init__(self):
            self.models = {}
            self.metadata = {}

        def register_model(self, name, model, metadata=None):
            self.models[name] = model
            self.metadata[name] = metadata or {}
            return True

        def get_model(self, name, version=None):
            if name not in self.models:
                raise KeyError(f"Model '{name}' not found")
            return self.models[name]

        def list_models(self):
            return list(self.models.keys())

        def delete_model(self, name):
            if name in self.models:
                del self.models[name]
                del self.metadata[name]
                return True
            return False

        def get_metadata(self, name):
            return self.metadata.get(name, {})

        def update_metadata(self, name, metadata):
            if name in self.metadata:
                self.metadata[name].update(metadata)
                return True
            return False

    return MockModelRegistry()


@pytest.fixture(scope="function")
def mock_feature_store():
    """Mock feature store for testing."""

    class MockFeatureStore:
        def __init__(self):
            self.features = {}
            self.feature_groups = {}

        def store_features(self, feature_group, features, metadata=None):
            self.feature_groups[feature_group] = {
                "features": features,
                "metadata": metadata or {},
            }

            # Store individual features
            for feature_name, feature_data in features.items():
                self.features[f"{feature_group}.{feature_name}"] = feature_data

        def get_features(self, feature_group, feature_names=None):
            if feature_group not in self.feature_groups:
                raise KeyError(f"Feature group '{feature_group}' not found")

            features = self.feature_groups[feature_group]["features"]

            if feature_names:
                return {
                    name: features[name] for name in feature_names if name in features
                }

            return features

        def list_feature_groups(self):
            return list(self.feature_groups.keys())

        def delete_feature_group(self, feature_group):
            if feature_group in self.feature_groups:
                # Remove individual features
                features = self.feature_groups[feature_group]["features"]
                for feature_name in features:
                    del self.features[f"{feature_group}.{feature_name}"]

                del self.feature_groups[feature_group]
                return True
            return False

    return MockFeatureStore()


@pytest.fixture(scope="function")
def sample_model_config():
    """Sample model configuration for testing."""
    return {
        "model_name": "test_classifier",
        "model_type": "classification",
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": 42,
        },
        "preprocessing": {
            "scaling": "standard",
            "encoding": "one_hot",
            "feature_selection": "variance_threshold",
        },
        "validation": {
            "method": "cross_validation",
            "folds": 5,
            "metrics": ["accuracy", "precision", "recall", "f1"],
        },
        "deployment": {
            "environment": "production",
            "version": "1.0.0",
            "endpoint": "/api/v1/predict",
        },
    }


@pytest.fixture(scope="function")
def mock_data_pipeline():
    """Mock data pipeline for testing."""

    class MockDataPipeline:
        def __init__(self):
            self.steps = []
            self.is_fitted = False

        def add_step(self, name, transformer):
            self.steps.append((name, transformer))

        def fit(self, X, y=None):
            self.is_fitted = True
            return self

        def transform(self, X):
            if not self.is_fitted:
                raise ValueError("Pipeline is not fitted yet.")

            # Mock transformation - just return the input
            return X

        def fit_transform(self, X, y=None):
            return self.fit(X, y).transform(X)

        def get_feature_names_out(self, input_features=None):
            if input_features is None:
                return [f"feature_{i}" for i in range(5)]
            return input_features

    return MockDataPipeline()


@pytest.fixture(scope="function")
def sample_model_metrics():
    """Sample model metrics for testing."""
    return {
        "classification_metrics": {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "auc_roc": 0.91,
            "confusion_matrix": [[45, 5], [8, 42]],
            "classification_report": {
                "0": {"precision": 0.85, "recall": 0.90, "f1-score": 0.87},
                "1": {"precision": 0.89, "recall": 0.84, "f1-score": 0.86},
            },
        },
        "regression_metrics": {
            "mse": 0.15,
            "rmse": 0.39,
            "mae": 0.31,
            "r2_score": 0.78,
            "explained_variance": 0.80,
        },
        "training_metrics": {
            "training_time": 45.2,
            "memory_usage": 256.7,
            "convergence_iterations": 150,
            "final_loss": 0.023,
        },
    }


@pytest.fixture(scope="function")
def mock_model_file(temp_directory):
    """Create mock model file for testing."""
    model_path = os.path.join(temp_directory, "test_model.pkl")

    # Create a simple mock model file
    import pickle

    mock_model_data = {
        "model_type": "test_classifier",
        "version": "1.0.0",
        "features": ["feature_1", "feature_2", "feature_3"],
        "metadata": {"created_at": "2024-01-15T12:00:00Z", "accuracy": 0.85},
    }

    with open(model_path, "wb") as f:
        pickle.dump(mock_model_data, f)

    return model_path


@pytest.fixture(scope="function")
def mock_experiment_tracker():
    """Mock experiment tracker for testing."""

    class MockExperimentTracker:
        def __init__(self):
            self.experiments = {}
            self.current_experiment = None

        def start_experiment(self, name, description=None):
            experiment_id = f"exp_{len(self.experiments) + 1}"
            self.experiments[experiment_id] = {
                "name": name,
                "description": description,
                "metrics": {},
                "parameters": {},
                "artifacts": {},
                "status": "running",
            }
            self.current_experiment = experiment_id
            return experiment_id

        def log_metric(self, key, value, step=None):
            if self.current_experiment:
                if key not in self.experiments[self.current_experiment]["metrics"]:
                    self.experiments[self.current_experiment]["metrics"][key] = []
                self.experiments[self.current_experiment]["metrics"][key].append(
                    {"value": value, "step": step}
                )

        def log_parameter(self, key, value):
            if self.current_experiment:
                self.experiments[self.current_experiment]["parameters"][key] = value

        def log_artifact(self, artifact_path, artifact_name=None):
            if self.current_experiment:
                name = artifact_name or os.path.basename(artifact_path)
                self.experiments[self.current_experiment]["artifacts"][name] = (
                    artifact_path
                )

        def end_experiment(self):
            if self.current_experiment:
                self.experiments[self.current_experiment]["status"] = "completed"
                self.current_experiment = None

        def get_experiment(self, experiment_id):
            return self.experiments.get(experiment_id)

        def list_experiments(self):
            return list(self.experiments.keys())

    return MockExperimentTracker()


@pytest.fixture(scope="function")
def sample_hyperparameter_space():
    """Sample hyperparameter space for testing."""
    return {
        "random_forest": {
            "n_estimators": [50, 100, 200, 300],
            "max_depth": [5, 10, 15, 20, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features": ["sqrt", "log2", None],
        },
        "logistic_regression": {
            "C": [0.001, 0.01, 0.1, 1, 10, 100],
            "penalty": ["l1", "l2", "elasticnet"],
            "solver": ["liblinear", "saga", "lbfgs"],
            "max_iter": [100, 500, 1000],
        },
        "neural_network": {
            "hidden_layer_sizes": [(50,), (100,), (50, 50), (100, 50)],
            "activation": ["relu", "tanh", "logistic"],
            "learning_rate": [0.001, 0.01, 0.1],
            "batch_size": [32, 64, 128],
            "epochs": [50, 100, 200],
        },
    }


@pytest.fixture(scope="function")
def mock_model_deployment():
    """Mock model deployment service for testing."""

    class MockModelDeployment:
        def __init__(self):
            self.deployed_models = {}
            self.deployment_history = []

        def deploy_model(self, model_name, model_path, endpoint, version="1.0.0"):
            deployment_id = f"deploy_{len(self.deployed_models) + 1}"

            deployment_info = {
                "model_name": model_name,
                "model_path": model_path,
                "endpoint": endpoint,
                "version": version,
                "status": "deployed",
                "deployed_at": "2024-01-15T12:00:00Z",
            }

            self.deployed_models[deployment_id] = deployment_info
            self.deployment_history.append(deployment_info)

            return deployment_id

        def undeploy_model(self, deployment_id):
            if deployment_id in self.deployed_models:
                self.deployed_models[deployment_id]["status"] = "undeployed"
                return True
            return False

        def get_deployment_status(self, deployment_id):
            return self.deployed_models.get(deployment_id, {}).get(
                "status", "not_found"
            )

        def list_deployments(self):
            return list(self.deployed_models.keys())

        def predict(self, deployment_id, data):
            if deployment_id not in self.deployed_models:
                raise ValueError(f"Deployment {deployment_id} not found")

            if self.deployed_models[deployment_id]["status"] != "deployed":
                raise ValueError(f"Deployment {deployment_id} is not active")

            # Mock prediction
            if isinstance(data, list):
                return [0.8] * len(data)
            return 0.8

    return MockModelDeployment()
