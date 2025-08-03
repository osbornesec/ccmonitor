#!/usr/bin/env python3
"""
Tests for Integration and Deployment System

This test suite validates the integration and deployment capabilities including
configuration management, model versioning, database operations, and API endpoints.
"""

import asyncio
import json
import tempfile
import pytest
import shutil
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.integration_deployment_system import (
    IntegrationDeploymentSystem,
    ConfigurationManager,
    ModelVersionManager,
    DatabaseManager,
    DeploymentEnvironment,
    DeploymentStatus,
    DeploymentConfig,
    SystemHealth,
    DeploymentMetrics
)


class TestDeploymentConfig:
    """Test deployment configuration data structure."""
    
    def test_deployment_config_creation(self):
        """Test creating deployment configuration."""
        config = DeploymentConfig(
            environment=DeploymentEnvironment.DEVELOPMENT,
            host="localhost",
            port=8001,
            workers=2,
            max_agents=5
        )
        
        assert config.environment == DeploymentEnvironment.DEVELOPMENT
        assert config.host == "localhost"
        assert config.port == 8001
        assert config.workers == 2
        assert config.max_agents == 5
        assert config.api_key_required is True  # Default value
    
    def test_deployment_config_defaults(self):
        """Test deployment configuration with defaults."""
        config = DeploymentConfig(environment=DeploymentEnvironment.PRODUCTION)
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.workers == 4
        assert config.max_agents == 10
        assert config.log_level == "INFO"
        assert config.cors_origins == ["*"]


class TestSystemHealth:
    """Test system health data structure."""
    
    def test_system_health_creation(self):
        """Test creating system health status."""
        health = SystemHealth(
            status="healthy",
            timestamp=datetime.now(),
            orchestrator_status="active",
            learning_system_status="active",
            monitoring_system_status="active",
            knowledge_framework_status="active",
            active_executions=2,
            total_agents=10,
            available_agents=8,
            system_load=45.2,
            memory_usage=67.8,
            disk_usage=23.1,
            database_status="active",
            api_response_time=0.12
        )
        
        assert health.status == "healthy"
        assert health.orchestrator_status == "active"
        assert health.active_executions == 2
        assert health.total_agents == 10
        assert health.available_agents == 8
        assert health.system_load == 45.2
        assert health.api_response_time == 0.12


class TestConfigurationManager:
    """Test configuration management functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create configuration manager with temporary directory."""
        return ConfigurationManager(temp_config_dir)
    
    def test_config_manager_initialization(self, config_manager):
        """Test configuration manager initialization."""
        assert config_manager.config_dir.exists()
        assert config_manager.logger is not None
    
    def test_create_default_config_development(self, config_manager):
        """Test creating default development configuration."""
        config = config_manager._create_default_config(DeploymentEnvironment.DEVELOPMENT)
        
        assert config.environment == DeploymentEnvironment.DEVELOPMENT
        assert config.port == 8001
        assert config.workers == 2
        assert config.api_key_required is False
        assert config.log_level == "DEBUG"
    
    def test_create_default_config_production(self, config_manager):
        """Test creating default production configuration."""
        config = config_manager._create_default_config(DeploymentEnvironment.PRODUCTION)
        
        assert config.environment == DeploymentEnvironment.PRODUCTION
        assert config.port == 8000
        assert config.workers == 8
        assert config.max_agents == 20
        assert config.auto_scaling is True
        assert config.cors_origins == ["https://yourapp.com"]
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading configuration."""
        # Create and save config
        original_config = DeploymentConfig(
            environment=DeploymentEnvironment.STAGING,
            host="staging.example.com",
            port=8002,
            workers=6,
            max_agents=15
        )
        
        config_manager.save_config(original_config)
        
        # Load config
        loaded_config = config_manager.load_config(DeploymentEnvironment.STAGING)
        
        assert loaded_config.environment == DeploymentEnvironment.STAGING
        assert loaded_config.host == "staging.example.com"
        assert loaded_config.port == 8002
        assert loaded_config.workers == 6
        assert loaded_config.max_agents == 15
    
    def test_load_nonexistent_config(self, config_manager):
        """Test loading configuration that doesn't exist."""
        config = config_manager.load_config(DeploymentEnvironment.TESTING)
        
        # Should create default config
        assert config.environment == DeploymentEnvironment.TESTING
        assert config.port == 8003
        assert config.workers == 1
        assert config.max_agents == 4


class TestModelVersionManager:
    """Test ML model version management."""
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create temporary models directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def model_manager(self, temp_models_dir):
        """Create model version manager with temporary directory."""
        return ModelVersionManager(temp_models_dir)
    
    @pytest.fixture
    def mock_learning_system(self):
        """Create mock learning system."""
        learning_system = Mock()
        learning_system.performance_predictor.is_trained = True
        learning_system.agent_optimizer.is_trained = True
        learning_system.performance_history = ["metric1", "metric2"]
        learning_system.export_models = Mock()
        return learning_system
    
    def test_model_manager_initialization(self, model_manager):
        """Test model version manager initialization."""
        assert model_manager.models_dir.exists()
        assert model_manager.logger is not None
    
    def test_create_version(self, model_manager, mock_learning_system):
        """Test creating new model version."""
        version_id = model_manager.create_version(mock_learning_system)
        
        assert version_id.startswith("v")
        assert len(version_id) > 10  # Should have timestamp
        
        # Check version directory exists
        version_dir = model_manager.models_dir / version_id
        assert version_dir.exists()
        
        # Check metadata file exists
        metadata_file = version_dir / "metadata.json"
        assert metadata_file.exists()
        
        # Verify export_models was called
        mock_learning_system.export_models.assert_called_once_with(str(version_dir))
    
    def test_deploy_version(self, model_manager, mock_learning_system):
        """Test deploying model version."""
        # Create version first
        version_id = model_manager.create_version(mock_learning_system)
        
        # Deploy version
        success = model_manager.deploy_version(version_id, DeploymentEnvironment.DEVELOPMENT)
        
        assert success is True
        
        # Check deployment symlink exists
        deployment_dir = model_manager.models_dir / "deployed_development"
        assert deployment_dir.exists()
        assert deployment_dir.is_symlink()
    
    def test_deploy_nonexistent_version(self, model_manager):
        """Test deploying version that doesn't exist."""
        success = model_manager.deploy_version("nonexistent_version", DeploymentEnvironment.DEVELOPMENT)
        
        assert success is False
    
    def test_list_versions(self, model_manager, mock_learning_system):
        """Test listing model versions."""
        # Initially no versions
        versions = model_manager.list_versions()
        assert len(versions) == 0
        
        # Create a version
        version_id = model_manager.create_version(mock_learning_system)
        
        # List versions
        versions = model_manager.list_versions()
        assert len(versions) == 1
        assert versions[0]["version_id"] == version_id
    
    def test_get_current_version(self, model_manager, mock_learning_system):
        """Test getting currently deployed version."""
        # No version deployed initially
        current = model_manager.get_current_version(DeploymentEnvironment.DEVELOPMENT)
        assert current is None
        
        # Create and deploy version
        version_id = model_manager.create_version(mock_learning_system)
        model_manager.deploy_version(version_id, DeploymentEnvironment.DEVELOPMENT)
        
        # Get current version
        current = model_manager.get_current_version(DeploymentEnvironment.DEVELOPMENT)
        assert current == version_id


class TestDatabaseManager:
    """Test database management functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create database manager with temporary database."""
        return DatabaseManager(temp_db_path)
    
    def test_db_manager_initialization(self, db_manager):
        """Test database manager initialization."""
        assert db_manager.db_path.exists()
        assert db_manager.logger is not None
    
    def test_initialize_database(self, db_manager):
        """Test database schema initialization."""
        db_manager.initialize_database()
        
        # Check that tables were created
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'orchestration_executions',
                'agent_performance',
                'system_health_log',
                'deployment_history',
                'api_usage_log',
                'error_log'
            ]
            
            for table in expected_tables:
                assert table in tables
    
    def test_migrate_database(self, db_manager):
        """Test database migration."""
        # Should complete without error
        db_manager.migrate_database()
        
        # Verify tables exist after migration
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            assert table_count >= 6  # At least 6 main tables
    
    def test_get_database_stats(self, db_manager):
        """Test getting database statistics."""
        db_manager.initialize_database()
        
        stats = db_manager.get_database_stats()
        
        assert "orchestration_executions_count" in stats
        assert "agent_performance_count" in stats
        assert "database_size_mb" in stats
        assert "executions_last_24h" in stats
        
        # All counts should be 0 for new database
        assert stats["orchestration_executions_count"] == 0
        assert stats["agent_performance_count"] == 0
    
    def test_backup_database(self, db_manager):
        """Test database backup functionality."""
        db_manager.initialize_database()
        
        with tempfile.TemporaryDirectory() as backup_dir:
            backup_path = db_manager.backup_database(backup_dir)
            
            assert backup_path is not None
            assert Path(backup_path).exists()
            assert backup_path.endswith(".tar.gz")


class TestIntegrationDeploymentSystem:
    """Test the main integration deployment system."""
    
    @pytest.fixture
    def temp_system_dir(self):
        """Create temporary system directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def deployment_system(self, temp_system_dir):
        """Create integration deployment system."""
        config_dir = Path(temp_system_dir) / "config"
        return IntegrationDeploymentSystem(str(config_dir))
    
    def test_system_initialization(self, deployment_system):
        """Test deployment system initialization."""
        assert deployment_system.config_manager is not None
        assert deployment_system.model_manager is not None
        assert deployment_system.db_manager is not None
        assert deployment_system.deployment_status == DeploymentStatus.STOPPED
        assert deployment_system.logger is not None
    
    @pytest.mark.asyncio
    async def test_get_system_health(self, deployment_system):
        """Test getting system health status."""
        with patch('psutil.cpu_percent', return_value=45.2), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock psutil objects
            mock_memory.return_value.percent = 67.8
            mock_disk.return_value.percent = 23.1
            
            health = await deployment_system.get_system_health()
            
            assert isinstance(health, SystemHealth)
            assert health.status in ["healthy", "degraded", "error"]
            assert health.system_load == 45.2
            assert health.memory_usage == 67.8
            assert health.disk_usage == 23.1
    
    @pytest.mark.asyncio
    async def test_deploy_development(self, deployment_system):
        """Test deploying to development environment."""
        with patch.object(deployment_system, '_initialize_components') as mock_init, \
             patch.object(deployment_system, '_start_health_monitoring') as mock_health:
            
            mock_init.return_value = None
            mock_health.return_value = None
            
            success = await deployment_system.deploy(DeploymentEnvironment.DEVELOPMENT)
            
            assert success is True
            assert deployment_system.deployment_status == DeploymentStatus.DEPLOYED
            assert deployment_system.current_environment == DeploymentEnvironment.DEVELOPMENT
            assert deployment_system.current_config is not None
            assert len(deployment_system.deployment_metrics) == 1
    
    @pytest.mark.asyncio
    async def test_deploy_with_version(self, deployment_system):
        """Test deploying with specific model version."""
        with patch.object(deployment_system, '_initialize_components') as mock_init, \
             patch.object(deployment_system, '_start_health_monitoring') as mock_health, \
             patch.object(deployment_system.model_manager, 'deploy_version', return_value=True) as mock_deploy:
            
            mock_init.return_value = None
            mock_health.return_value = None
            
            success = await deployment_system.deploy(
                DeploymentEnvironment.STAGING,
                version="v20240101_120000"
            )
            
            assert success is True
            mock_deploy.assert_called_once_with("v20240101_120000", DeploymentEnvironment.STAGING)
    
    @pytest.mark.asyncio
    async def test_deploy_with_config_overrides(self, deployment_system):
        """Test deploying with configuration overrides."""
        config_overrides = {
            "max_agents": 20,
            "workers": 8,
            "port": 9000
        }
        
        with patch.object(deployment_system, '_initialize_components') as mock_init, \
             patch.object(deployment_system, '_start_health_monitoring') as mock_health:
            
            mock_init.return_value = None
            mock_health.return_value = None
            
            success = await deployment_system.deploy(
                DeploymentEnvironment.DEVELOPMENT,
                config_overrides=config_overrides
            )
            
            assert success is True
            assert deployment_system.current_config.max_agents == 20
            assert deployment_system.current_config.workers == 8
            assert deployment_system.current_config.port == 9000
    
    @pytest.mark.asyncio
    async def test_deploy_failure(self, deployment_system):
        """Test deployment failure handling."""
        with patch.object(deployment_system, '_initialize_components', side_effect=Exception("Init failed")):
            
            success = await deployment_system.deploy(DeploymentEnvironment.DEVELOPMENT)
            
            assert success is False
            assert deployment_system.deployment_status == DeploymentStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_stop_deployment(self, deployment_system):
        """Test stopping deployment."""
        # Mock deployed state
        deployment_system.deployment_status = DeploymentStatus.DEPLOYED
        deployment_system.learning_system = Mock()
        deployment_system.orchestrator = Mock()
        
        await deployment_system.stop_deployment()
        
        assert deployment_system.deployment_status == DeploymentStatus.STOPPED
        assert deployment_system.orchestrator is None
        assert deployment_system.learning_system is None
    
    def test_initialize_api_without_fastapi(self, deployment_system):
        """Test API initialization when FastAPI not available."""
        with patch('PRPs.scripts.integration_deployment_system.FASTAPI_AVAILABLE', False):
            config = DeploymentConfig(environment=DeploymentEnvironment.DEVELOPMENT)
            deployment_system._initialize_api(config)
            
            # Should not create app
            assert deployment_system.app is None
    
    @pytest.mark.asyncio
    async def test_record_health_status(self, deployment_system):
        """Test recording health status to database."""
        # Initialize database
        deployment_system.db_manager.initialize_database()
        
        health = SystemHealth(
            status="healthy",
            timestamp=datetime.now(),
            orchestrator_status="active",
            learning_system_status="active",
            monitoring_system_status="active",
            knowledge_framework_status="active",
            active_executions=1,
            total_agents=5,
            available_agents=4,
            system_load=30.0,
            memory_usage=50.0,
            disk_usage=25.0,
            database_status="active",
            api_response_time=0.1
        )
        
        await deployment_system._record_health_status(health)
        
        # Verify record was created
        import sqlite3
        with sqlite3.connect(deployment_system.db_manager.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM system_health_log")
            count = cursor.fetchone()[0]
            assert count == 1


class TestAPIEndpoints:
    """Test API endpoint functionality (if FastAPI available)."""
    
    @pytest.fixture
    def deployment_system_with_api(self):
        """Create deployment system with API initialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            system = IntegrationDeploymentSystem(temp_dir)
            
            # Mock components
            system.orchestrator = Mock()
            system.learning_system = Mock()
            system.monitoring_system = Mock()
            system.knowledge_framework = Mock()
            
            # Initialize API if FastAPI available
            if hasattr(system, 'app') and system.app is None:
                try:
                    config = DeploymentConfig(environment=DeploymentEnvironment.DEVELOPMENT)
                    system._initialize_api(config)
                except Exception:
                    pass  # FastAPI might not be available
            
            yield system
    
    def test_api_initialization(self, deployment_system_with_api):
        """Test API initialization."""
        # Test depends on FastAPI availability
        if deployment_system_with_api.app is not None:
            assert deployment_system_with_api.app.title == "Multi-Agent PRP Orchestration API"
        else:
            # FastAPI not available, skip test
            pytest.skip("FastAPI not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])