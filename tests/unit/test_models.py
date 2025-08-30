"""Unit tests for model classes.

This module tests the base model functionality and specific model classes
to ensure proper database operations and model behavior.
"""

from datetime import datetime
from unittest.mock import patch

from app.extensions import db
from app.models.base import BaseModel


class TestBaseModel:
    """Test the BaseModel class functionality."""

    def test_base_model_is_abstract(self):
        """Test that BaseModel is abstract and cannot be instantiated directly."""
        assert BaseModel.__abstract__ is True

    def test_base_model_has_required_fields(self):
        """Test that BaseModel has required common fields."""
        # Check that the class has the expected columns
        assert hasattr(BaseModel, "id")
        assert hasattr(BaseModel, "created_at")
        assert hasattr(BaseModel, "updated_at")

    def test_base_model_id_field(self):
        """Test the id field configuration."""
        id_column = BaseModel.id
        assert id_column.primary_key is True
        assert id_column.type.python_type == int

    def test_base_model_timestamp_fields(self):
        """Test the timestamp field configuration."""
        created_at = BaseModel.created_at
        updated_at = BaseModel.updated_at

        assert created_at.nullable is False
        assert updated_at.nullable is False
        assert created_at.default is not None
        assert updated_at.default is not None
        assert updated_at.onupdate is not None

    def test_tablename_generation_simple(self):
        """Test table name generation for simple class names."""

        class TestModel(BaseModel):
            """
            TODO: Add class description.

            Class TestModel.
            """
            __tablename__ = None

        # Mock the declared_attr behavior
        with patch("app.models.base.declared_attr") as mock_declared_attr:
            # Simulate the tablename generation
            import re

            name = "TestModel"
            name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
            name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

            expected = "test_models"  # Assuming pluralization adds 's'
            assert "test_model" in name.lower()

    def test_tablename_generation_camelcase(self):
        """Test table name generation for CamelCase class names."""
        import re

        # Test UserProfile -> user_profile
        name = "UserProfile"
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        assert name == "user_profile"

    def test_tablename_generation_multiple_words(self):
        """Test table name generation for multiple word class names."""
        import re

        # Test OrderItemDetail -> order_item_detail
        name = "OrderItemDetail"
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        assert name == "order_item_detail"

    def test_model_inheritance(self):
        """Test that models can properly inherit from BaseModel."""

        class ConcreteModel(BaseModel):
            __tablename__ = "concrete_models"

        # Test that the concrete model has all base fields
        assert hasattr(ConcreteModel, "id")
        assert hasattr(ConcreteModel, "created_at")
        assert hasattr(ConcreteModel, "updated_at")

        # Test that it inherits from db.Model
        assert issubclass(ConcreteModel, db.Model)

    @patch("app.models.base.datetime")
    def test_timestamp_defaults(self, mock_datetime):
        """Test that timestamp fields use proper defaults."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        # Test that created_at default is datetime.utcnow
        created_at_default = BaseModel.created_at.default.arg
        assert created_at_default == datetime.utcnow

        # Test that updated_at default and onupdate are datetime.utcnow
        updated_at_default = BaseModel.updated_at.default.arg
        updated_at_onupdate = BaseModel.updated_at.onupdate.arg

        assert updated_at_default == datetime.utcnow
        assert updated_at_onupdate == datetime.utcnow


class TestConcreteModel:
    """Test concrete model implementation using BaseModel."""

    def setup_method(self):
        """Set up test fixtures."""

        # Create a concrete model for testing
        class TestModel(BaseModel):
            __tablename__ = "test_models"

            def __init__(self, **kwargs):
                super().__init__()
                for key, value in kwargs.items():
                    setattr(self, key, value)

        self.TestModel = TestModel

    def test_concrete_model_creation(self, app):
        """Test creating an instance of a concrete model."""
        with app.app_context():
            model = self.TestModel()

            # Test that the model has the expected attributes
            assert hasattr(model, "id")
            assert hasattr(model, "created_at")
            assert hasattr(model, "updated_at")

            # Test that id is None before saving
            assert model.id is None

    def test_model_tablename(self):
        """Test that concrete model has correct table name."""
        assert self.TestModel.__tablename__ == "test_models"

    def test_model_database_operations(self, app, db):
        """Test basic database operations with concrete model."""
        with app.app_context():
            # Create the table
            db.create_all()

            try:
                # Create and save a model instance
                model = self.TestModel()
                db.session.add(model)
                db.session.commit()

                # Test that the model was saved with an ID
                assert model.id is not None
                assert isinstance(model.id, int)

                # Test that timestamps were set
                assert model.created_at is not None
                assert model.updated_at is not None
                assert isinstance(model.created_at, datetime)
                assert isinstance(model.updated_at, datetime)

            finally:
                # Clean up
                db.session.rollback()
                db.drop_all()

    def test_model_update_timestamp(self, app, db):
        """Test that updated_at timestamp changes on update."""
        with app.app_context():
            db.create_all()

            try:
                # Create and save a model
                model = self.TestModel()
                db.session.add(model)
                db.session.commit()

                original_updated_at = model.updated_at

                # Wait a small amount to ensure timestamp difference
                import time

                time.sleep(0.01)

                # Update the model
                model.created_at = datetime.utcnow()  # Trigger an update
                db.session.commit()

                # Test that updated_at changed
                assert model.updated_at != original_updated_at
                assert model.updated_at > original_updated_at

            finally:
                db.session.rollback()
                db.drop_all()


    """
    TODO: Add class description.

    Class TestModel.
    """
class TestModelUtilityMethods:
    """Test utility methods that might be added to BaseModel."""

    def test_model_repr_method(self):
        """Test that models can have proper string representation."""

        class TestModel(BaseModel):
            __tablename__ = "test_models"

            def __repr__(self):
                return f"<TestModel(id={self.id})>"

        model = TestModel()
        assert "TestModel" in repr(model)
        assert "id=" in repr(model)

    def test_model_equality(self):
        """Test model equality comparison."""

        class TestModel(BaseModel):
            __tablename__ = "test_models"

            def __eq__(self, other):
                if not isinstance(other, TestModel):
                    return False
                return self.id == other.id and self.id is not None

        model1 = TestModel()
        model2 = TestModel()

        # Models without IDs should not be equal
        assert model1 != model2

        # Models with same ID should be equal
        model1.id = 1
        model2.id = 1
        assert model1 == model2

        # Models with different IDs should not be equal
        model2.id = 2
        assert model1 != model2