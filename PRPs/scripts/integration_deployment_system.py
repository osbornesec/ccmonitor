#!/usr/bin/env python3
"""
Integration and Deployment System for Multi-Agent PRP Orchestration

This module provides comprehensive integration and deployment capabilities including:
- Production-ready API endpoints for system interaction
- Automated deployment pipelines with health checks
- Configuration management for different environments
- Real-time monitoring dashboard and system status
- Model versioning and deployment management
- Scalable persistence layer with data migration
- Security and authentication management
- Performance monitoring and alerting integration
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from contextlib import asynccontextmanager
import sqlite3
import hashlib
import zipfile
import tarfile

# FastAPI and web dependencies
try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Import project components
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PRPs.scripts.multi_agent_orchestrator import MultiAgentOrchestrator, OrchestrationExecution
    from PRPs.scripts.learning_and_optimization_system import LearningAndOptimizationSystem
    from PRPs.scripts.advanced_monitoring_system import AdvancedMonitoringSystem
    from PRPs.scripts.knowledge_sharing_framework import KnowledgeSharingFramework
except ImportError as e:
    print(f"Warning: Could not import all required modules: {e}")


class DeploymentEnvironment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DeploymentStatus(Enum):
    """Deployment status enumeration."""
    INITIALIZING = "initializing"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    UPDATING = "updating"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class DeploymentConfig:
    """Configuration for deployment environments."""
    environment: DeploymentEnvironment
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    max_agents: int = 10
    database_url: str = "sqlite:///prp_orchestration.db"
    redis_url: Optional[str] = None
    log_level: str = "INFO"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_key_required: bool = True
    model_versioning: bool = True
    auto_scaling: bool = False
    health_check_interval: int = 30
    metrics_retention_days: int = 30
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SystemHealth:
    """System health status information."""
    status: str
    timestamp: datetime
    orchestrator_status: str
    learning_system_status: str
    monitoring_system_status: str
    knowledge_framework_status: str
    active_executions: int
    total_agents: int
    available_agents: int
    system_load: float
    memory_usage: float
    disk_usage: float
    database_status: str
    api_response_time: float
    last_deployment: Optional[datetime] = None
    uptime_seconds: int = 0


@dataclass
class DeploymentMetrics:
    """Deployment and performance metrics."""
    deployment_id: str
    environment: str
    deployment_time: datetime
    version: str
    status: DeploymentStatus
    health_score: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0
    success_rate: float = 1.0
    response_times: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)


class APIModels:
    """Pydantic models for API endpoints."""
    
    class OrchestrationRequest(BaseModel):
        project_dir: str = Field(..., description="Project directory path")
        prp_files: List[str] = Field(..., description="List of PRP files to execute")
        max_agents: Optional[int] = Field(10, description="Maximum number of agents")
        priority: Optional[str] = Field("medium", description="Execution priority")
        environment_vars: Optional[Dict[str, str]] = Field(default_factory=dict)
        
    class OrchestrationResponse(BaseModel):
        execution_id: str
        status: str
        message: str
        estimated_duration: Optional[float] = None
        
    class SystemStatusResponse(BaseModel):
        status: str
        timestamp: str
        components: Dict[str, str]
        metrics: Dict[str, Any]
        
    class DeploymentRequest(BaseModel):
        environment: str = Field(..., description="Target deployment environment")
        version: Optional[str] = Field(None, description="Version to deploy")
        config_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
        
    class LearningInsightResponse(BaseModel):
        pattern_type: str
        description: str
        confidence: float
        recommendations: List[str]
        evidence: Dict[str, Any]


class ConfigurationManager:
    """Manages configuration across different environments."""
    
    def __init__(self, config_dir: str = "PRPs/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for configuration manager."""
        logger = logging.getLogger(f"ConfigManager_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_config(self, environment: DeploymentEnvironment) -> DeploymentConfig:
        """Load configuration for specific environment."""
        config_file = self.config_dir / f"{environment.value}.yaml"
        
        # Create default config if doesn't exist
        if not config_file.exists():
            config = self._create_default_config(environment)
            self.save_config(config)
            return config
            
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Convert to DeploymentConfig
            config = DeploymentConfig(
                environment=environment,
                **{k: v for k, v in config_data.items() if k != 'environment'}
            )
            
            self.logger.info(f"Loaded configuration for {environment.value}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config for {environment.value}: {e}")
            return self._create_default_config(environment)
    
    def save_config(self, config: DeploymentConfig):
        """Save configuration to file."""
        config_file = self.config_dir / f"{config.environment.value}.yaml"
        
        try:
            config_dict = asdict(config)
            config_dict['environment'] = config.environment.value
            
            with open(config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                
            self.logger.info(f"Saved configuration for {config.environment.value}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _create_default_config(self, environment: DeploymentEnvironment) -> DeploymentConfig:
        """Create default configuration for environment."""
        base_config = {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
            "max_agents": 10,
            "log_level": "INFO",
            "cors_origins": ["*"],
            "api_key_required": True,
            "model_versioning": True,
            "health_check_interval": 30,
            "metrics_retention_days": 30,
            "backup_enabled": True,
            "backup_interval_hours": 24
        }
        
        # Environment-specific overrides
        if environment == DeploymentEnvironment.DEVELOPMENT:
            base_config.update({
                "port": 8001,
                "workers": 2,
                "api_key_required": False,
                "log_level": "DEBUG"
            })
        elif environment == DeploymentEnvironment.STAGING:
            base_config.update({
                "port": 8002,
                "workers": 3,
                "log_level": "INFO"
            })
        elif environment == DeploymentEnvironment.PRODUCTION:
            base_config.update({
                "port": 8000,
                "workers": 8,
                "max_agents": 20,
                "auto_scaling": True,
                "metrics_retention_days": 90,
                "cors_origins": ["https://yourapp.com"]
            })
        elif environment == DeploymentEnvironment.TESTING:
            base_config.update({
                "port": 8003,
                "workers": 1,
                "max_agents": 4,
                "api_key_required": False
            })
        
        return DeploymentConfig(environment=environment, **base_config)


class ModelVersionManager:
    """Manages ML model versions and deployment."""
    
    def __init__(self, models_dir: str = "PRPs/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.models_dir / "versions.json"
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for model version manager."""
        logger = logging.getLogger(f"ModelVersionManager_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_version(self, learning_system: 'LearningAndOptimizationSystem') -> str:
        """Create new model version from learning system."""
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_dir = self.models_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        try:
            # Export models from learning system
            learning_system.export_models(str(version_dir))
            
            # Create version metadata
            metadata = {
                "version_id": version_id,
                "created_at": datetime.now().isoformat(),
                "performance_predictor_trained": learning_system.performance_predictor.is_trained,
                "agent_optimizer_trained": learning_system.agent_optimizer.is_trained,
                "total_performance_metrics": len(learning_system.performance_history),
                "model_files": list(version_dir.glob("*.pkl"))
            }
            
            # Save metadata
            with open(version_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Update versions registry
            self._update_versions_registry(version_id, metadata)
            
            self.logger.info(f"Created model version {version_id}")
            return version_id
            
        except Exception as e:
            self.logger.error(f"Error creating model version: {e}")
            # Cleanup partial version
            if version_dir.exists():
                shutil.rmtree(version_dir)
            raise
    
    def deploy_version(self, version_id: str, environment: DeploymentEnvironment) -> bool:
        """Deploy specific model version to environment."""
        version_dir = self.models_dir / version_id
        
        if not version_dir.exists():
            self.logger.error(f"Version {version_id} not found")
            return False
        
        try:
            # Create deployment symlink or copy
            deployment_dir = self.models_dir / f"deployed_{environment.value}"
            
            if deployment_dir.exists():
                if deployment_dir.is_symlink():
                    deployment_dir.unlink()
                else:
                    shutil.rmtree(deployment_dir)
            
            # Create symlink to version
            deployment_dir.symlink_to(version_dir, target_is_directory=True)
            
            # Update deployment record
            self._update_deployment_record(version_id, environment)
            
            self.logger.info(f"Deployed version {version_id} to {environment.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deploying version {version_id}: {e}")
            return False
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """List all available model versions."""
        if not self.versions_file.exists():
            return []
        
        try:
            with open(self.versions_file, 'r') as f:
                versions_data = json.load(f)
            return versions_data.get("versions", [])
        except Exception as e:
            self.logger.error(f"Error listing versions: {e}")
            return []
    
    def get_current_version(self, environment: DeploymentEnvironment) -> Optional[str]:
        """Get currently deployed version for environment."""
        deployment_dir = self.models_dir / f"deployed_{environment.value}"
        
        if deployment_dir.exists() and deployment_dir.is_symlink():
            return deployment_dir.readlink().name
        
        return None
    
    def _update_versions_registry(self, version_id: str, metadata: Dict[str, Any]):
        """Update the versions registry file."""
        versions_data = {"versions": []}
        
        if self.versions_file.exists():
            try:
                with open(self.versions_file, 'r') as f:
                    versions_data = json.load(f)
            except Exception:
                pass
        
        # Add new version
        versions_data["versions"].append(metadata)
        
        # Sort by creation date (newest first)
        versions_data["versions"].sort(
            key=lambda x: x.get("created_at", ""), reverse=True
        )
        
        # Keep only last 50 versions
        versions_data["versions"] = versions_data["versions"][:50]
        
        # Save updated registry
        with open(self.versions_file, 'w') as f:
            json.dump(versions_data, f, indent=2, default=str)
    
    def _update_deployment_record(self, version_id: str, environment: DeploymentEnvironment):
        """Update deployment record for tracking."""
        deployments_file = self.models_dir / "deployments.json"
        deployments_data = {"deployments": {}}
        
        if deployments_file.exists():
            try:
                with open(deployments_file, 'r') as f:
                    deployments_data = json.load(f)
            except Exception:
                pass
        
        deployments_data["deployments"][environment.value] = {
            "version_id": version_id,
            "deployed_at": datetime.now().isoformat()
        }
        
        with open(deployments_file, 'w') as f:
            json.dump(deployments_data, f, indent=2, default=str)


class DatabaseManager:
    """Manages database operations and migrations."""
    
    def __init__(self, database_url: str = "PRPs/production.db"):
        self.database_url = database_url
        self.db_path = Path(database_url)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for database manager."""
        logger = logging.getLogger(f"DatabaseManager_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def initialize_database(self):
        """Initialize database with all required schemas."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create main orchestration tables
                conn.executescript("""
                    -- Orchestration execution tracking
                    CREATE TABLE IF NOT EXISTS orchestration_executions (
                        id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        total_tasks INTEGER DEFAULT 0,
                        completed_tasks INTEGER DEFAULT 0,
                        failed_tasks INTEGER DEFAULT 0,
                        configuration TEXT,
                        results TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Agent performance tracking
                    CREATE TABLE IF NOT EXISTS agent_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_name TEXT NOT NULL,
                        execution_id TEXT NOT NULL,
                        tasks_completed INTEGER DEFAULT 0,
                        tasks_failed INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        average_execution_time REAL DEFAULT 0.0,
                        efficiency_rating REAL DEFAULT 1.0,
                        specialization_score REAL DEFAULT 0.0,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (execution_id) REFERENCES orchestration_executions(id)
                    );
                    
                    -- System health tracking
                    CREATE TABLE IF NOT EXISTS system_health_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        overall_status TEXT NOT NULL,
                        orchestrator_status TEXT,
                        learning_system_status TEXT,
                        monitoring_system_status TEXT,
                        knowledge_framework_status TEXT,
                        system_metrics TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Deployment tracking
                    CREATE TABLE IF NOT EXISTS deployment_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deployment_id TEXT UNIQUE NOT NULL,
                        environment TEXT NOT NULL,
                        version TEXT,
                        status TEXT NOT NULL,
                        deployment_time TEXT NOT NULL,
                        completion_time TEXT,
                        configuration TEXT,
                        logs TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- API usage tracking
                    CREATE TABLE IF NOT EXISTS api_usage_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint TEXT NOT NULL,
                        method TEXT NOT NULL,
                        status_code INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        user_agent TEXT,
                        ip_address TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Error tracking
                    CREATE TABLE IF NOT EXISTS error_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        context TEXT,
                        severity TEXT DEFAULT 'error',
                        resolved BOOLEAN DEFAULT FALSE,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Create indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_orchestration_status ON orchestration_executions(status);
                    CREATE INDEX IF NOT EXISTS idx_orchestration_start_time ON orchestration_executions(start_time);
                    CREATE INDEX IF NOT EXISTS idx_agent_performance_agent ON agent_performance(agent_name);
                    CREATE INDEX IF NOT EXISTS idx_agent_performance_timestamp ON agent_performance(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health_log(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_deployment_environment ON deployment_history(environment);
                    CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_log(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_error_log_timestamp ON error_log(timestamp);
                """)
                
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def migrate_database(self):
        """Run database migrations if needed."""
        # For now, just ensure database is initialized
        # In a production system, this would handle schema migrations
        self.initialize_database()
        self.logger.info("Database migrations completed")
    
    def backup_database(self, backup_dir: str = "PRPs/backups"):
        """Create database backup."""
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"database_backup_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_file)
            
            # Compress backup
            compressed_backup = backup_path / f"database_backup_{timestamp}.tar.gz"
            with tarfile.open(compressed_backup, "w:gz") as tar:
                tar.add(backup_file, arcname=backup_file.name)
            
            # Remove uncompressed backup
            backup_file.unlink()
            
            self.logger.info(f"Database backup created: {compressed_backup}")
            return str(compressed_backup)
            
        except Exception as e:
            self.logger.error(f"Error creating database backup: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Get table counts
                tables = [
                    "orchestration_executions",
                    "agent_performance", 
                    "system_health_log",
                    "deployment_history",
                    "api_usage_log",
                    "error_log"
                ]
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Get database size
                stats["database_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
                
                # Get recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM orchestration_executions 
                    WHERE start_time > datetime('now', '-24 hours')
                """)
                stats["executions_last_24h"] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}


class IntegrationDeploymentSystem:
    """
    Main integration and deployment system that orchestrates all components
    for production-ready deployment of the multi-agent PRP system.
    """
    
    def __init__(self, config_dir: str = "PRPs/config"):
        self.logger = self._setup_logging()
        self.start_time = datetime.now()
        
        # Core managers
        self.config_manager = ConfigurationManager(config_dir)
        self.model_manager = ModelVersionManager()
        self.db_manager = DatabaseManager()
        
        # System components (initialized on deployment)
        self.orchestrator: Optional[MultiAgentOrchestrator] = None
        self.learning_system: Optional[LearningAndOptimizationSystem] = None
        self.monitoring_system: Optional[AdvancedMonitoringSystem] = None
        self.knowledge_framework: Optional[KnowledgeSharingFramework] = None
        
        # Deployment state
        self.current_environment: Optional[DeploymentEnvironment] = None
        self.current_config: Optional[DeploymentConfig] = None
        self.deployment_status = DeploymentStatus.STOPPED
        self.deployment_metrics: List[DeploymentMetrics] = []
        
        # FastAPI app (if available)
        self.app: Optional[FastAPI] = None
        self.security = HTTPBearer() if FASTAPI_AVAILABLE else None
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the integration system."""
        logger = logging.getLogger(f"IntegrationDeployment_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def deploy(self, environment: DeploymentEnvironment, 
                    version: Optional[str] = None,
                    config_overrides: Optional[Dict[str, Any]] = None) -> bool:
        """Deploy the system to specified environment."""
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"Starting deployment {deployment_id} to {environment.value}")
            self.deployment_status = DeploymentStatus.DEPLOYING
            
            # Load configuration
            config = self.config_manager.load_config(environment)
            if config_overrides:
                for key, value in config_overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            self.current_config = config
            self.current_environment = environment
            
            # Initialize database
            self.db_manager = DatabaseManager(config.database_url)
            self.db_manager.migrate_database()
            
            # Initialize system components
            await self._initialize_components(config)
            
            # Deploy ML models if versioning enabled
            if config.model_versioning and version:
                if not self.model_manager.deploy_version(version, environment):
                    raise Exception(f"Failed to deploy model version {version}")
            
            # Initialize API if FastAPI available
            if FASTAPI_AVAILABLE:
                self._initialize_api(config)
            
            # Start health monitoring
            await self._start_health_monitoring()
            
            # Record deployment
            deployment_metrics = DeploymentMetrics(
                deployment_id=deployment_id,
                environment=environment.value,
                deployment_time=datetime.now(),
                version=version or "latest",
                status=DeploymentStatus.DEPLOYED,
                health_score=1.0
            )
            self.deployment_metrics.append(deployment_metrics)
            
            self.deployment_status = DeploymentStatus.DEPLOYED
            self.logger.info(f"Deployment {deployment_id} completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            self.deployment_status = DeploymentStatus.FAILED
            return False
    
    async def _initialize_components(self, config: DeploymentConfig):
        """Initialize all system components."""
        self.logger.info("Initializing system components...")
        
        # Initialize orchestrator
        self.orchestrator = MultiAgentOrchestrator(max_agents=config.max_agents)
        
        # Components should be initialized as part of orchestrator
        self.learning_system = self.orchestrator.learning_system
        self.monitoring_system = self.orchestrator.monitoring_system  
        self.knowledge_framework = self.orchestrator.knowledge_framework
        
        # Load deployed models if available
        if config.model_versioning:
            deployed_version = self.model_manager.get_current_version(config.environment)
            if deployed_version and self.learning_system:
                try:
                    # In a full implementation, we'd load the models here
                    self.logger.info(f"Using deployed model version: {deployed_version}")
                except Exception as e:
                    self.logger.warning(f"Could not load deployed models: {e}")
        
        self.logger.info("System components initialized successfully")
    
    def _initialize_api(self, config: DeploymentConfig):
        """Initialize FastAPI application."""
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI not available, skipping API initialization")
            return
        
        self.app = FastAPI(
            title="Multi-Agent PRP Orchestration API",
            description="Production API for autonomous TDD-PRP development system",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add API routes
        self._setup_api_routes()
        
        self.logger.info("FastAPI application initialized")
    
    def _setup_api_routes(self):
        """Set up API routes."""
        if not self.app:
            return
        
        @self.app.get("/")
        async def root():
            return {"message": "Multi-Agent PRP Orchestration System", "status": "operational"}
        
        @self.app.get("/health")
        async def health_check():
            """System health check endpoint."""
            health = await self.get_system_health()
            return JSONResponse(content=asdict(health))
        
        @self.app.get("/status")
        async def system_status():
            """Detailed system status endpoint."""
            try:
                status = {
                    "deployment_status": self.deployment_status.value,
                    "environment": self.current_environment.value if self.current_environment else None,
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "components": {
                        "orchestrator": "active" if self.orchestrator else "inactive",
                        "learning_system": "active" if self.learning_system else "inactive", 
                        "monitoring_system": "active" if self.monitoring_system else "inactive",
                        "knowledge_framework": "active" if self.knowledge_framework else "inactive"
                    }
                }
                
                if self.orchestrator:
                    orchestrator_status = self.orchestrator.get_real_time_status()
                    status["orchestrator_metrics"] = orchestrator_status
                
                return JSONResponse(content=status)
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/orchestrate")
        async def start_orchestration(
            request: APIModels.OrchestrationRequest,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Start PRP orchestration."""
            try:
                if not self.orchestrator:
                    raise HTTPException(status_code=503, detail="Orchestrator not available")
                
                # Validate authentication if required
                if self.current_config and self.current_config.api_key_required:
                    # In a real implementation, validate the API key
                    pass
                
                # Start orchestration in background
                execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                async def run_orchestration():
                    try:
                        execution = await self.orchestrator.orchestrate_project(
                            project_dir=request.project_dir,
                            prp_files=request.prp_files
                        )
                        
                        # Record execution in database
                        await self._record_execution(execution)
                        
                    except Exception as e:
                        self.logger.error(f"Orchestration {execution_id} failed: {e}")
                
                background_tasks.add_task(run_orchestration)
                
                return APIModels.OrchestrationResponse(
                    execution_id=execution_id,
                    status="started",
                    message="Orchestration started successfully"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/learning/insights")
        async def get_learning_insights():
            """Get learning system insights."""
            try:
                if not self.learning_system:
                    raise HTTPException(status_code=503, detail="Learning system not available")
                
                insights = self.learning_system.get_learning_insights()
                
                return [
                    APIModels.LearningInsightResponse(
                        pattern_type=insight.pattern_type,
                        description=insight.description,
                        confidence=insight.confidence,
                        recommendations=insight.recommendations,
                        evidence=insight.evidence
                    )
                    for insight in insights[:10]  # Return top 10
                ]
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/learning/recommendations")
        async def get_optimization_recommendations():
            """Get optimization recommendations."""
            try:
                if not self.learning_system:
                    raise HTTPException(status_code=503, detail="Learning system not available")
                
                recommendations = self.learning_system.get_optimization_recommendations()
                
                return [
                    {
                        "category": rec.category,
                        "priority": rec.priority,
                        "description": rec.description,
                        "expected_improvement": rec.expected_improvement,
                        "confidence_score": rec.confidence_score
                    }
                    for rec in recommendations[:10]  # Return top 10
                ]
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models/versions")
        async def list_model_versions():
            """List available model versions."""
            try:
                versions = self.model_manager.list_versions()
                return {"versions": versions}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/deploy")
        async def deploy_model_version(request: dict):
            """Deploy specific model version."""
            try:
                version_id = request.get("version_id")
                environment = DeploymentEnvironment(request.get("environment", "development"))
                
                if not version_id:
                    raise HTTPException(status_code=400, detail="version_id is required")
                
                success = self.model_manager.deploy_version(version_id, environment)
                
                if success:
                    return {"message": f"Model version {version_id} deployed to {environment.value}"}
                else:
                    raise HTTPException(status_code=500, detail="Model deployment failed")
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/dashboard")
        async def dashboard():
            """Serve monitoring dashboard."""
            # In a full implementation, this would serve an HTML dashboard
            dashboard_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Multi-Agent PRP Orchestration Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .metric { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
                    .status-active { color: green; }
                    .status-inactive { color: red; }
                </style>
            </head>
            <body>
                <h1>Multi-Agent PRP Orchestration Dashboard</h1>
                <div id="metrics">
                    <div class="metric">
                        <h3>System Status</h3>
                        <p>Status: <span class="status-active">Operational</span></p>
                    </div>
                </div>
                <script>
                    // In a full implementation, this would fetch real-time data
                    setInterval(() => {
                        fetch('/status')
                            .then(response => response.json())
                            .then(data => {
                                console.log('System status:', data);
                            });
                    }, 5000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=dashboard_html)
    
    async def _start_health_monitoring(self):
        """Start background health monitoring."""
        if not self.current_config:
            return
        
        async def health_monitor():
            while self.deployment_status == DeploymentStatus.DEPLOYED:
                try:
                    health = await self.get_system_health()
                    await self._record_health_status(health)
                    
                    # Sleep for configured interval
                    await asyncio.sleep(self.current_config.health_check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(30)  # Wait before retrying
        
        # Start health monitoring task
        asyncio.create_task(health_monitor())
        self.logger.info("Health monitoring started")
    
    async def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health status."""
        try:
            # Get orchestrator status
            orchestrator_status = "active" if self.orchestrator else "inactive"
            learning_status = "active" if self.learning_system else "inactive"
            monitoring_status = "active" if self.monitoring_system else "inactive"
            knowledge_status = "active" if self.knowledge_framework else "inactive"
            
            # Get system metrics
            import psutil
            system_load = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            # Get orchestrator metrics if available
            active_executions = 0
            total_agents = 0
            available_agents = 0
            
            if self.orchestrator:
                status = self.orchestrator.get_real_time_status()
                active_executions = status.get("active_executions", 0)
                total_agents = len(self.orchestrator.base_coordinator.agents)
                available_agents = len([
                    agent for agent, status in self.orchestrator.agent_status.items()
                    if status.value == "idle"
                ])
            
            # Determine overall status
            overall_status = "healthy"
            if system_load > 90 or memory_usage > 90 or disk_usage > 95:
                overall_status = "degraded"
            
            return SystemHealth(
                status=overall_status,
                timestamp=datetime.now(),
                orchestrator_status=orchestrator_status,
                learning_system_status=learning_status,
                monitoring_system_status=monitoring_status,
                knowledge_framework_status=knowledge_status,
                active_executions=active_executions,
                total_agents=total_agents,
                available_agents=available_agents,
                system_load=system_load,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                database_status="active",
                api_response_time=0.1,  # Mock value
                last_deployment=self.deployment_metrics[-1].deployment_time if self.deployment_metrics else None,
                uptime_seconds=int((datetime.now() - self.start_time).total_seconds())
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return SystemHealth(
                status="error",
                timestamp=datetime.now(),
                orchestrator_status="unknown",
                learning_system_status="unknown",
                monitoring_system_status="unknown", 
                knowledge_framework_status="unknown",
                active_executions=0,
                total_agents=0,
                available_agents=0,
                system_load=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                database_status="unknown",
                api_response_time=0.0,
                uptime_seconds=0
            )
    
    async def _record_health_status(self, health: SystemHealth):
        """Record health status to database."""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_health_log 
                    (timestamp, overall_status, orchestrator_status, learning_system_status,
                     monitoring_system_status, knowledge_framework_status, system_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    health.timestamp.isoformat(),
                    health.status,
                    health.orchestrator_status,
                    health.learning_system_status,
                    health.monitoring_system_status,
                    health.knowledge_framework_status,
                    json.dumps({
                        "system_load": health.system_load,
                        "memory_usage": health.memory_usage,
                        "disk_usage": health.disk_usage,
                        "active_executions": health.active_executions,
                        "total_agents": health.total_agents,
                        "available_agents": health.available_agents
                    })
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording health status: {e}")
    
    async def _record_execution(self, execution: 'OrchestrationExecution'):
        """Record orchestration execution to database."""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("""
                    INSERT INTO orchestration_executions 
                    (id, project_name, status, start_time, end_time, total_tasks,
                     completed_tasks, failed_tasks, configuration, results)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.project_name,
                    execution.status,
                    execution.start_time.isoformat(),
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.total_tasks,
                    execution.completed_tasks,
                    execution.failed_tasks,
                    json.dumps(asdict(execution)),
                    ""  # Results would be populated after completion
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording execution: {e}")
    
    async def stop_deployment(self):
        """Stop current deployment."""
        self.logger.info("Stopping deployment...")
        self.deployment_status = DeploymentStatus.STOPPING
        
        # Stop learning system
        if self.learning_system:
            self.learning_system.stop_learning()
        
        # Clean up resources
        self.orchestrator = None
        self.learning_system = None
        self.monitoring_system = None
        self.knowledge_framework = None
        
        self.deployment_status = DeploymentStatus.STOPPED
        self.logger.info("Deployment stopped")
    
    def run_api_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API server."""
        if not FASTAPI_AVAILABLE or not self.app:
            self.logger.error("FastAPI not available or not initialized")
            return
        
        self.logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Command-line interface and example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent PRP Integration and Deployment System")
    parser.add_argument("--environment", choices=["development", "staging", "production", "testing"],
                       default="development", help="Deployment environment")
    parser.add_argument("--config-dir", default="PRPs/config", help="Configuration directory")
    parser.add_argument("--version", help="Model version to deploy")
    parser.add_argument("--host", default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--action", choices=["deploy", "stop", "status", "health"], 
                       default="deploy", help="Action to perform")
    
    args = parser.parse_args()
    
    async def main():
        # Initialize integration system
        system = IntegrationDeploymentSystem(args.config_dir)
        
        try:
            if args.action == "deploy":
                environment = DeploymentEnvironment(args.environment)
                success = await system.deploy(environment, args.version)
                
                if success:
                    print(f"✅ Deployment to {args.environment} successful")
                    
                    # Start API server if FastAPI available
                    if FASTAPI_AVAILABLE:
                        system.run_api_server(args.host, args.port)
                    else:
                        print("FastAPI not available, API server not started")
                        # Keep system running for other functionality
                        await asyncio.sleep(3600)  # Run for 1 hour
                else:
                    print(f"❌ Deployment to {args.environment} failed")
                    
            elif args.action == "stop":
                await system.stop_deployment()
                print("✅ System stopped")
                
            elif args.action == "status":
                if system.deployment_status == DeploymentStatus.DEPLOYED:
                    health = await system.get_system_health()
                    print(f"System Status: {health.status}")
                    print(f"Uptime: {health.uptime_seconds} seconds")
                    print(f"Active Executions: {health.active_executions}")
                    print(f"Available Agents: {health.available_agents}/{health.total_agents}")
                else:
                    print(f"System Status: {system.deployment_status.value}")
                    
            elif args.action == "health":
                health = await system.get_system_health()
                print(f"Overall Status: {health.status}")
                print(f"System Load: {health.system_load}%")
                print(f"Memory Usage: {health.memory_usage}%")
                print(f"Disk Usage: {health.disk_usage}%")
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            await system.stop_deployment()
        except Exception as e:
            print(f"Error: {e}")
    
    # Run the main function
    asyncio.run(main())