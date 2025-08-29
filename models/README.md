# ML Models Directory

This directory contains machine learning model files and related artifacts.

## Directory Structure

```
models/
├── README.md              # This file
├── trained/               # Trained model files
│   ├── model_v1.pkl      # Serialized models
│   ├── model_v2.joblib   # Joblib format models
│   └── pytorch_model.pth # PyTorch models
├── preprocessing/         # Preprocessing artifacts
│   ├── scaler.pkl        # Feature scalers
│   ├── encoder.pkl       # Label encoders
│   └── vectorizer.pkl    # Text vectorizers
├── metadata/              # Model metadata
│   ├── model_info.json   # Model information
│   ├── feature_names.json # Feature definitions
│   └── metrics.json      # Performance metrics
└── checkpoints/           # Training checkpoints
    ├── epoch_10.pth      # Training snapshots
    └── best_model.pth    # Best performing model
```

## Supported Model Formats

### Scikit-learn
- `.pkl` - Pickle format (default)
- `.joblib` - Joblib format (recommended for large models)

### PyTorch
- `.pth` - PyTorch state dict
- `.pt` - PyTorch model

### TensorFlow
- `.h5` - Keras HDF5 format
- `.pb` - TensorFlow SavedModel

### ONNX
- `.onnx` - Open Neural Network Exchange format

## Model Naming Convention

```
{model_name}_{version}_{date}.{extension}
```

Examples:
- `fraud_detector_v1_20240101.pkl`
- `sentiment_classifier_v2_20240115.joblib`
- `recommendation_engine_v3_20240201.pth`

## Model Metadata

Each model should have accompanying metadata in JSON format:

```json
{
  "name": "fraud_detector",
  "version": "1.0.0",
  "description": "Credit card fraud detection model",
  "algorithm": "Random Forest",
  "framework": "scikit-learn",
  "created_at": "2024-01-01T00:00:00Z",
  "trained_on": "fraud_dataset_v1",
  "features": ["amount", "merchant_category", "time_of_day"],
  "target": "is_fraud",
  "metrics": {
    "accuracy": 0.95,
    "precision": 0.92,
    "recall": 0.89,
    "f1_score": 0.90
  },
  "file_path": "trained/fraud_detector_v1_20240101.pkl",
  "file_size": "2.5MB",
  "checksum": "sha256:abc123..."
}
```

## Loading Models in Services

Models are automatically loaded by ML services that inherit from `BaseMLService`:

```python
from app.services.base import BaseMLService

class FraudDetectionService(BaseMLService):
    model_name = "fraud_detector"
    model_version = "v1"
    
    def predict(self, data):
        # Model is available as self.model
        return self.model.predict(data)
```

## Model Versioning

- Use semantic versioning (v1.0.0, v1.1.0, v2.0.0)
- Keep multiple versions for A/B testing
- Document breaking changes between versions
- Maintain backward compatibility when possible

## Performance Optimization

- Use model caching for frequently accessed models
- Implement lazy loading for large models
- Consider model quantization for deployment
- Monitor memory usage and loading times

## Security Considerations

- Validate model files before loading
- Use checksums to verify model integrity
- Avoid loading models from untrusted sources
- Implement access controls for sensitive models

## Deployment Notes

- Models are automatically discovered by the ML service registry
- Use environment variables to specify model paths
- Consider using model serving platforms for production
- Implement health checks for model availability

## Backup and Recovery

- Regularly backup trained models
- Store models in version control (Git LFS for large files)
- Maintain model training scripts for reproducibility
- Document model dependencies and requirements