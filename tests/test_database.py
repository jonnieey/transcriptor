import os

import pytest
from sqlalchemy import inspect, text

from transcriptor.database import Database


# Test models needed for testing (simplified)
class TestDatabase:
    @pytest.fixture
    def memory_db(self):
        """Fixture for in-memory database"""
        db = Database(":memory:")
        db.init_db()
        return db

    @pytest.fixture
    def file_db(self, tmp_path):
        """Fixture for file-based database with temporary path"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.init_db()
        yield db
        # Cleanup
        if os.path.exists(db_file):
            os.unlink(db_file)

    def test_init_memory_db(self, memory_db):
        """Test initialization with in-memory database"""
        assert memory_db.db_file == ":memory:"
        assert memory_db.engine is not None

        # Verify tables are created
        inspector = inspect(memory_db.engine)
        assert "clients" in inspector.get_table_names()

    def test_init_file_db(self, file_db, tmp_path):
        """Test initialization with file-based database"""
        db_file = tmp_path / "test.db"
        assert str(db_file) == file_db.db_file
        assert os.path.exists(db_file)
        assert file_db.engine is not None

        # Verify tables are created
        inspector = inspect(file_db.engine)
        assert "clients" in inspector.get_table_names()

    def test_foreign_keys_enabled(self, memory_db):
        """Test that foreign key constraints are enabled"""
        with memory_db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).fetchone()
            assert result[0] == 1  # Should be enabled
