#!/usr/bin/env python3
"""
Knowledge Sharing Framework for Multi-Agent PRP Orchestration

This framework enables real-time knowledge sharing between agents during execution:
- Shared knowledge graph for cross-agent learning
- Pattern recognition for common development workflows
- Real-time context sharing between agents
- Knowledge persistence and retrieval mechanisms
- Conflict resolution for overlapping agent expertise

Usage:
    framework = KnowledgeSharingFramework()
    await framework.share_knowledge(agent_name, knowledge_type, data)
    insights = await framework.get_relevant_insights(task_context)
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
import hashlib

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class KnowledgeType(Enum):
    """Types of knowledge that can be shared between agents."""
    PATTERN = "pattern"
    SOLUTION = "solution"
    ERROR = "error"
    OPTIMIZATION = "optimization"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    WORKFLOW = "workflow"


class KnowledgeRelevance(Enum):
    """Relevance levels for knowledge sharing."""
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    MINIMAL = 0.2


@dataclass
class KnowledgeItem:
    """Represents a piece of knowledge shared between agents."""
    id: str
    source_agent: str
    knowledge_type: KnowledgeType
    domain: str
    title: str
    content: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 1.0
    relevance_score: float = 1.0
    tags: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)


@dataclass
class KnowledgeQuery:
    """Query for retrieving relevant knowledge."""
    requesting_agent: str
    task_domain: str
    task_description: str
    context: Dict[str, Any]
    knowledge_types: List[KnowledgeType] = field(default_factory=lambda: list(KnowledgeType))
    max_results: int = 10
    min_relevance: float = 0.3


@dataclass
class AgentExpertise:
    """Tracks an agent's areas of expertise based on shared knowledge."""
    agent_name: str
    domain_scores: Dict[str, float] = field(default_factory=dict)
    knowledge_contributions: int = 0
    successful_applications: int = 0
    expertise_rating: float = 1.0
    specialization_areas: List[str] = field(default_factory=list)
    collaboration_history: Dict[str, int] = field(default_factory=dict)


@dataclass
class CollaborationPattern:
    """Represents a successful collaboration pattern between agents."""
    id: str
    agent_pair: Tuple[str, str]
    task_type: str
    success_count: int = 1
    total_attempts: int = 1
    average_completion_time: float = 0.0
    knowledge_shared: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


class KnowledgeSharingFramework:
    """
    Advanced knowledge sharing framework that enables real-time learning
    and collaboration between agents in the multi-agent orchestration system.
    """

    def __init__(self, db_path: str = "PRPs/knowledge_graph.db"):
        self.db_path = Path(db_path)
        self.logger = self._setup_logging()
        
        # In-memory knowledge stores for fast access
        self.knowledge_graph: Dict[str, KnowledgeItem] = {}
        self.agent_expertise: Dict[str, AgentExpertise] = {}
        self.collaboration_patterns: Dict[str, CollaborationPattern] = {}
        
        # Real-time sharing state
        self.active_sharing_sessions: Dict[str, Dict[str, Any]] = {}
        self.knowledge_subscriptions: Dict[str, List[str]] = {}  # agent -> knowledge types
        
        # Performance tracking
        self.sharing_metrics: Dict[str, Any] = {
            "total_shares": 0,
            "successful_applications": 0,
            "knowledge_reuse_rate": 0.0,
            "collaboration_efficiency": 1.0
        }
        
        # Initialize database and load existing knowledge
        self._initialize_database()
        self._load_existing_knowledge()
        
        self.logger.info("Knowledge Sharing Framework initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for knowledge sharing framework."""
        logger = logging.getLogger("KnowledgeSharingFramework")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize_database(self):
        """Initialize SQLite database for persistent knowledge storage."""
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            # Knowledge items table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    source_agent TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 1.0,
                    relevance_score REAL DEFAULT 1.0,
                    tags TEXT DEFAULT '[]',
                    related_items TEXT DEFAULT '[]'
                )
            ''')
            
            # Agent expertise table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_expertise (
                    agent_name TEXT PRIMARY KEY,
                    domain_scores TEXT NOT NULL,
                    knowledge_contributions INTEGER DEFAULT 0,
                    successful_applications INTEGER DEFAULT 0,
                    expertise_rating REAL DEFAULT 1.0,
                    specialization_areas TEXT DEFAULT '[]',
                    collaboration_history TEXT DEFAULT '{}'
                )
            ''')
            
            # Collaboration patterns table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collaboration_patterns (
                    id TEXT PRIMARY KEY,
                    agent_pair TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    success_count INTEGER DEFAULT 1,
                    total_attempts INTEGER DEFAULT 1,
                    average_completion_time REAL DEFAULT 0.0,
                    knowledge_shared TEXT DEFAULT '[]',
                    best_practices TEXT DEFAULT '[]'
                )
            ''')
            
            # Knowledge usage tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT NOT NULL,
                    using_agent TEXT NOT NULL,
                    task_context TEXT NOT NULL,
                    usage_timestamp TEXT NOT NULL,
                    was_successful BOOLEAN NOT NULL,
                    performance_impact REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()

    def _load_existing_knowledge(self):
        """Load existing knowledge from database into memory."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Load knowledge items
                cursor = conn.execute('SELECT * FROM knowledge_items')
                for row in cursor.fetchall():
                    knowledge_item = KnowledgeItem(
                        id=row[0],
                        source_agent=row[1],
                        knowledge_type=KnowledgeType(row[2]),
                        domain=row[3],
                        title=row[4],
                        content=json.loads(row[5]),
                        context=json.loads(row[6]),
                        timestamp=datetime.fromisoformat(row[7]),
                        usage_count=row[8],
                        success_rate=row[9],
                        relevance_score=row[10],
                        tags=json.loads(row[11]),
                        related_items=json.loads(row[12])
                    )
                    self.knowledge_graph[knowledge_item.id] = knowledge_item
                
                # Load agent expertise
                cursor = conn.execute('SELECT * FROM agent_expertise')
                for row in cursor.fetchall():
                    expertise = AgentExpertise(
                        agent_name=row[0],
                        domain_scores=json.loads(row[1]),
                        knowledge_contributions=row[2],
                        successful_applications=row[3],
                        expertise_rating=row[4],
                        specialization_areas=json.loads(row[5]),
                        collaboration_history=json.loads(row[6])
                    )
                    self.agent_expertise[expertise.agent_name] = expertise
                
                # Load collaboration patterns
                cursor = conn.execute('SELECT * FROM collaboration_patterns')
                for row in cursor.fetchall():
                    pattern = CollaborationPattern(
                        id=row[0],
                        agent_pair=tuple(row[1].split(',')),
                        task_type=row[2],
                        success_count=row[3],
                        total_attempts=row[4],
                        average_completion_time=row[5],
                        knowledge_shared=json.loads(row[6]),
                        best_practices=json.loads(row[7])
                    )
                    self.collaboration_patterns[pattern.id] = pattern
        
        except Exception as e:
            self.logger.error(f"Error loading existing knowledge: {e}")
        
        self.logger.info(f"Loaded {len(self.knowledge_graph)} knowledge items, "
                        f"{len(self.agent_expertise)} agent profiles, "
                        f"{len(self.collaboration_patterns)} collaboration patterns")

    async def share_knowledge(self, agent_name: str, knowledge_type: KnowledgeType, 
                            domain: str, title: str, content: Dict[str, Any], 
                            context: Dict[str, Any], tags: List[str] = None) -> str:
        """
        Share knowledge from an agent to the global knowledge graph.
        
        Args:
            agent_name: Name of the agent sharing knowledge
            knowledge_type: Type of knowledge being shared
            domain: Domain/specialty area
            title: Human-readable title for the knowledge
            content: The actual knowledge content
            context: Context in which this knowledge was discovered/used
            tags: Optional tags for categorization
            
        Returns:
            Knowledge item ID
        """
        # Generate unique knowledge ID
        knowledge_id = self._generate_knowledge_id(agent_name, title, content)
        
        # Create knowledge item
        knowledge_item = KnowledgeItem(
            id=knowledge_id,
            source_agent=agent_name,
            knowledge_type=knowledge_type,
            domain=domain,
            title=title,
            content=content,
            context=context,
            tags=tags or []
        )
        
        # Calculate relevance score
        knowledge_item.relevance_score = self._calculate_relevance_score(knowledge_item)
        
        # Add to knowledge graph
        self.knowledge_graph[knowledge_id] = knowledge_item
        
        # Update agent expertise
        await self._update_agent_expertise(agent_name, domain, knowledge_type)
        
        # Find and link related knowledge
        await self._link_related_knowledge(knowledge_item)
        
        # Persist to database
        await self._persist_knowledge_item(knowledge_item)
        
        # Notify subscribed agents
        await self._notify_subscribers(knowledge_item)
        
        # Update metrics
        self.sharing_metrics["total_shares"] += 1
        
        self.logger.info(f"📚 Knowledge shared by {agent_name}: {title} ({knowledge_type.value})")
        
        return knowledge_id

    def _generate_knowledge_id(self, agent_name: str, title: str, content: Dict[str, Any]) -> str:
        """Generate unique ID for knowledge item."""
        content_str = json.dumps(content, sort_keys=True)
        hash_input = f"{agent_name}:{title}:{content_str}:{int(time.time())}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _calculate_relevance_score(self, knowledge_item: KnowledgeItem) -> float:
        """Calculate relevance score for knowledge item."""
        score = 1.0
        
        # Boost score for certain knowledge types
        type_multipliers = {
            KnowledgeType.SOLUTION: 1.2,
            KnowledgeType.ERROR: 1.1,
            KnowledgeType.OPTIMIZATION: 1.15,
            KnowledgeType.BEST_PRACTICE: 1.3,
            KnowledgeType.PATTERN: 1.1
        }
        score *= type_multipliers.get(knowledge_item.knowledge_type, 1.0)
        
        # Boost based on content richness
        content_items = len(knowledge_item.content)
        if content_items > 3:
            score *= 1.1
        
        # Boost based on context richness
        context_items = len(knowledge_item.context)
        if context_items > 2:
            score *= 1.05
        
        return min(score, 2.0)  # Cap at 2.0

    async def _update_agent_expertise(self, agent_name: str, domain: str, 
                                    knowledge_type: KnowledgeType):
        """Update agent expertise based on knowledge contribution."""
        if agent_name not in self.agent_expertise:
            self.agent_expertise[agent_name] = AgentExpertise(agent_name=agent_name)
        
        expertise = self.agent_expertise[agent_name]
        
        # Update domain scores
        if domain not in expertise.domain_scores:
            expertise.domain_scores[domain] = 0.5
        
        expertise.domain_scores[domain] = min(1.0, expertise.domain_scores[domain] + 0.1)
        
        # Update contribution count
        expertise.knowledge_contributions += 1
        
        # Update specialization areas
        if domain not in expertise.specialization_areas and expertise.domain_scores[domain] > 0.7:
            expertise.specialization_areas.append(domain)
        
        # Recalculate expertise rating
        expertise.expertise_rating = (
            sum(expertise.domain_scores.values()) / len(expertise.domain_scores) +
            min(expertise.knowledge_contributions / 10, 0.5)
        )

    async def _link_related_knowledge(self, knowledge_item: KnowledgeItem):
        """Find and link related knowledge items."""
        related_items = []
        
        for existing_id, existing_item in self.knowledge_graph.items():
            if existing_id == knowledge_item.id:
                continue
            
            # Check for domain similarity
            if existing_item.domain == knowledge_item.domain:
                similarity_score = self._calculate_similarity(knowledge_item, existing_item)
                if similarity_score > 0.5:
                    related_items.append(existing_id)
            
            # Check for tag overlap
            tag_overlap = set(knowledge_item.tags) & set(existing_item.tags)
            if len(tag_overlap) > 0:
                related_items.append(existing_id)
        
        # Keep only top 5 most related items
        knowledge_item.related_items = related_items[:5]

    def _calculate_similarity(self, item1: KnowledgeItem, item2: KnowledgeItem) -> float:
        """Calculate similarity between two knowledge items."""
        similarity = 0.0
        
        # Domain match
        if item1.domain == item2.domain:
            similarity += 0.3
        
        # Knowledge type match
        if item1.knowledge_type == item2.knowledge_type:
            similarity += 0.3
        
        # Tag overlap
        if item1.tags and item2.tags:
            tag_overlap = len(set(item1.tags) & set(item2.tags))
            tag_similarity = tag_overlap / max(len(item1.tags), len(item2.tags))
            similarity += tag_similarity * 0.2
        
        # Content key overlap
        content1_keys = set(item1.content.keys())
        content2_keys = set(item2.content.keys())
        key_overlap = len(content1_keys & content2_keys)
        if content1_keys or content2_keys:
            key_similarity = key_overlap / len(content1_keys | content2_keys)
            similarity += key_similarity * 0.2
        
        return similarity

    async def _persist_knowledge_item(self, knowledge_item: KnowledgeItem):
        """Persist knowledge item to database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO knowledge_items 
                    (id, source_agent, knowledge_type, domain, title, content, context, 
                     timestamp, usage_count, success_rate, relevance_score, tags, related_items)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_item.id,
                    knowledge_item.source_agent,
                    knowledge_item.knowledge_type.value,
                    knowledge_item.domain,
                    knowledge_item.title,
                    json.dumps(knowledge_item.content),
                    json.dumps(knowledge_item.context),
                    knowledge_item.timestamp.isoformat(),
                    knowledge_item.usage_count,
                    knowledge_item.success_rate,
                    knowledge_item.relevance_score,
                    json.dumps(knowledge_item.tags),
                    json.dumps(knowledge_item.related_items)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error persisting knowledge item: {e}")

    async def _notify_subscribers(self, knowledge_item: KnowledgeItem):
        """Notify agents subscribed to this type of knowledge."""
        for agent_name, subscribed_types in self.knowledge_subscriptions.items():
            if (knowledge_item.knowledge_type.value in subscribed_types and 
                agent_name != knowledge_item.source_agent):
                
                await self._send_knowledge_notification(agent_name, knowledge_item)

    async def _send_knowledge_notification(self, agent_name: str, knowledge_item: KnowledgeItem):
        """Send knowledge notification to an agent."""
        notification = {
            "type": "knowledge_available",
            "knowledge_id": knowledge_item.id,
            "source_agent": knowledge_item.source_agent,
            "knowledge_type": knowledge_item.knowledge_type.value,
            "domain": knowledge_item.domain,
            "title": knowledge_item.title,
            "relevance_score": knowledge_item.relevance_score,
            "timestamp": knowledge_item.timestamp.isoformat()
        }
        
        self.logger.info(f"🔔 Notifying {agent_name} about new knowledge: {knowledge_item.title}")

    async def query_knowledge(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """
        Query the knowledge graph for relevant information.
        
        Args:
            query: KnowledgeQuery with search criteria
            
        Returns:
            List of relevant knowledge items sorted by relevance
        """
        relevant_items = []
        
        for knowledge_item in self.knowledge_graph.values():
            relevance = self._calculate_query_relevance(query, knowledge_item)
            
            if relevance >= query.min_relevance:
                relevant_items.append((knowledge_item, relevance))
        
        # Sort by relevance and limit results
        relevant_items.sort(key=lambda x: x[1], reverse=True)
        results = [item for item, _ in relevant_items[:query.max_results]]
        
        # Update usage statistics
        for item in results:
            item.usage_count += 1
            await self._record_knowledge_usage(query.requesting_agent, item.id, query.context)
        
        self.logger.info(f"🔍 Knowledge query by {query.requesting_agent}: "
                        f"found {len(results)} relevant items")
        
        return results

    def _calculate_query_relevance(self, query: KnowledgeQuery, 
                                 knowledge_item: KnowledgeItem) -> float:
        """Calculate relevance of knowledge item to query."""
        relevance = knowledge_item.relevance_score * 0.3
        
        # Domain match
        if knowledge_item.domain == query.task_domain:
            relevance += 0.4
        elif query.task_domain in knowledge_item.domain or knowledge_item.domain in query.task_domain:
            relevance += 0.2
        
        # Knowledge type match
        if knowledge_item.knowledge_type in query.knowledge_types or not query.knowledge_types:
            relevance += 0.2
        
        # Description similarity (simple keyword matching)
        query_words = set(query.task_description.lower().split())
        title_words = set(knowledge_item.title.lower().split())
        content_words = set(str(knowledge_item.content).lower().split())
        
        word_overlap = len(query_words & (title_words | content_words))
        if word_overlap > 0:
            relevance += min(word_overlap / len(query_words), 0.3)
        
        # Success rate boost
        relevance *= knowledge_item.success_rate
        
        # Recent knowledge boost
        age_days = (datetime.now() - knowledge_item.timestamp).days
        if age_days < 7:
            relevance *= 1.2
        elif age_days < 30:
            relevance *= 1.1
        
        return min(relevance, 2.0)

    async def _record_knowledge_usage(self, agent_name: str, knowledge_id: str, 
                                    context: Dict[str, Any]):
        """Record knowledge usage for analytics."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO knowledge_usage 
                    (knowledge_id, using_agent, task_context, usage_timestamp, 
                     was_successful, performance_impact)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    agent_name,
                    json.dumps(context),
                    datetime.now().isoformat(),
                    True,  # Will be updated later based on task outcome
                    0.0    # Will be updated later based on performance impact
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error recording knowledge usage: {e}")

    async def subscribe_to_knowledge(self, agent_name: str, 
                                   knowledge_types: List[KnowledgeType]):
        """Subscribe an agent to specific types of knowledge."""
        type_values = [kt.value for kt in knowledge_types]
        self.knowledge_subscriptions[agent_name] = type_values
        
        self.logger.info(f"📬 {agent_name} subscribed to knowledge types: {type_values}")

    async def record_collaboration(self, agent1: str, agent2: str, task_type: str, 
                                 completion_time: float, success: bool,
                                 knowledge_shared: List[str] = None):
        """Record a collaboration between two agents."""
        # Create collaboration pattern ID
        agent_pair = tuple(sorted([agent1, agent2]))
        pattern_id = f"{agent_pair[0]}_{agent_pair[1]}_{task_type}"
        
        if pattern_id in self.collaboration_patterns:
            pattern = self.collaboration_patterns[pattern_id]
            pattern.total_attempts += 1
            if success:
                pattern.success_count += 1
            
            # Update average completion time
            pattern.average_completion_time = (
                pattern.average_completion_time * 0.8 + completion_time * 0.2
            )
            
            if knowledge_shared:
                pattern.knowledge_shared.extend(knowledge_shared)
        else:
            pattern = CollaborationPattern(
                id=pattern_id,
                agent_pair=agent_pair,
                task_type=task_type,
                success_count=1 if success else 0,
                total_attempts=1,
                average_completion_time=completion_time,
                knowledge_shared=knowledge_shared or []
            )
            self.collaboration_patterns[pattern_id] = pattern
        
        # Update agent collaboration history
        for agent_name in [agent1, agent2]:
            other_agent = agent2 if agent_name == agent1 else agent1
            if agent_name in self.agent_expertise:
                expertise = self.agent_expertise[agent_name]
                if other_agent not in expertise.collaboration_history:
                    expertise.collaboration_history[other_agent] = 0
                expertise.collaboration_history[other_agent] += 1
        
        await self._persist_collaboration_pattern(pattern)
        
        self.logger.info(f"🤝 Recorded collaboration: {agent1} + {agent2} on {task_type}")

    async def _persist_collaboration_pattern(self, pattern: CollaborationPattern):
        """Persist collaboration pattern to database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO collaboration_patterns 
                    (id, agent_pair, task_type, success_count, total_attempts, 
                     average_completion_time, knowledge_shared, best_practices)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.id,
                    ','.join(pattern.agent_pair),
                    pattern.task_type,
                    pattern.success_count,
                    pattern.total_attempts,
                    pattern.average_completion_time,
                    json.dumps(pattern.knowledge_shared),
                    json.dumps(pattern.best_practices)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error persisting collaboration pattern: {e}")

    async def get_collaboration_recommendations(self, agent_name: str, 
                                              task_type: str) -> List[str]:
        """Get recommendations for agent collaboration based on historical patterns."""
        recommendations = []
        
        # Find successful collaboration patterns
        for pattern in self.collaboration_patterns.values():
            if (agent_name in pattern.agent_pair and 
                pattern.task_type == task_type and
                pattern.success_count / pattern.total_attempts > 0.7):
                
                other_agent = (pattern.agent_pair[1] if pattern.agent_pair[0] == agent_name 
                              else pattern.agent_pair[0])
                recommendations.append(other_agent)
        
        return recommendations

    async def extract_patterns(self, domain: str = None, 
                             min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Extract common patterns from the knowledge graph."""
        patterns = []
        
        # Group knowledge by domain and type
        domain_groups = {}
        for item in self.knowledge_graph.values():
            if domain and item.domain != domain:
                continue
            
            key = f"{item.domain}_{item.knowledge_type.value}"
            if key not in domain_groups:
                domain_groups[key] = []
            domain_groups[key].append(item)
        
        # Find patterns in each group
        for group_key, items in domain_groups.items():
            if len(items) >= min_occurrences:
                pattern = await self._analyze_pattern_group(group_key, items)
                if pattern:
                    patterns.append(pattern)
        
        return patterns

    async def _analyze_pattern_group(self, group_key: str, 
                                   items: List[KnowledgeItem]) -> Optional[Dict[str, Any]]:
        """Analyze a group of knowledge items to extract patterns."""
        # Find common elements
        common_tags = set(items[0].tags)
        for item in items[1:]:
            common_tags &= set(item.tags)
        
        # Find common content keys
        common_content_keys = set(items[0].content.keys())
        for item in items[1:]:
            common_content_keys &= set(item.content.keys())
        
        if len(common_tags) > 0 or len(common_content_keys) > 0:
            return {
                "pattern_id": f"pattern_{group_key}_{int(time.time())}",
                "group": group_key,
                "occurrences": len(items),
                "common_tags": list(common_tags),
                "common_content_keys": list(common_content_keys),
                "average_success_rate": sum(item.success_rate for item in items) / len(items),
                "contributing_agents": list(set(item.source_agent for item in items)),
                "time_span": {
                    "start": min(item.timestamp for item in items).isoformat(),
                    "end": max(item.timestamp for item in items).isoformat()
                }
            }
        
        return None

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge graph."""
        if not self.knowledge_graph:
            return {"total_items": 0}
        
        # Basic counts
        stats = {
            "total_items": len(self.knowledge_graph),
            "total_agents": len(self.agent_expertise),
            "collaboration_patterns": len(self.collaboration_patterns)
        }
        
        # Knowledge type distribution
        type_counts = {}
        for item in self.knowledge_graph.values():
            type_name = item.knowledge_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        stats["knowledge_types"] = type_counts
        
        # Domain distribution
        domain_counts = {}
        for item in self.knowledge_graph.values():
            domain_counts[item.domain] = domain_counts.get(item.domain, 0) + 1
        stats["domains"] = domain_counts
        
        # Usage statistics
        total_usage = sum(item.usage_count for item in self.knowledge_graph.values())
        avg_success_rate = (sum(item.success_rate for item in self.knowledge_graph.values()) / 
                           len(self.knowledge_graph))
        
        stats["usage_stats"] = {
            "total_usage": total_usage,
            "average_success_rate": avg_success_rate,
            "reuse_rate": total_usage / len(self.knowledge_graph) if len(self.knowledge_graph) > 0 else 0
        }
        
        # Top contributors
        contributor_counts = {}
        for item in self.knowledge_graph.values():
            agent = item.source_agent
            contributor_counts[agent] = contributor_counts.get(agent, 0) + 1
        
        top_contributors = sorted(contributor_counts.items(), 
                                key=lambda x: x[1], reverse=True)[:5]
        stats["top_contributors"] = top_contributors
        
        return stats

    async def cleanup_old_knowledge(self, max_age_days: int = 90, 
                                  min_usage_count: int = 1):
        """Clean up old, unused knowledge to maintain performance."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        items_to_remove = []
        
        for knowledge_id, item in self.knowledge_graph.items():
            if (item.timestamp < cutoff_date and 
                item.usage_count < min_usage_count and
                item.success_rate < 0.5):
                items_to_remove.append(knowledge_id)
        
        # Remove from memory
        for knowledge_id in items_to_remove:
            del self.knowledge_graph[knowledge_id]
        
        # Remove from database
        if items_to_remove:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    placeholders = ','.join(['?' for _ in items_to_remove])
                    conn.execute(f'DELETE FROM knowledge_items WHERE id IN ({placeholders})', 
                               items_to_remove)
                    conn.commit()
            except Exception as e:
                self.logger.error(f"Error cleaning up old knowledge: {e}")
        
        self.logger.info(f"🧹 Cleaned up {len(items_to_remove)} old knowledge items")
        
        return len(items_to_remove)


# Example usage and testing
async def main():
    """Example usage of the Knowledge Sharing Framework."""
    framework = KnowledgeSharingFramework()
    
    # Example: Share some knowledge
    await framework.share_knowledge(
        agent_name="python-specialist",
        knowledge_type=KnowledgeType.SOLUTION,
        domain="python",
        title="FastAPI Authentication Pattern",
        content={
            "pattern": "JWT with dependency injection",
            "code_example": "def get_current_user(token: str = Depends(oauth2_scheme))",
            "benefits": ["Reusable", "Secure", "Testable"]
        },
        context={
            "project_type": "web_api",
            "framework": "fastapi",
            "complexity": 6
        },
        tags=["authentication", "jwt", "fastapi", "security"]
    )
    
    # Example: Query for knowledge
    query = KnowledgeQuery(
        requesting_agent="react-specialist",
        task_domain="frontend",
        task_description="implement user authentication in React app",
        context={"framework": "react", "complexity": 5}
    )
    
    results = await framework.query_knowledge(query)
    print(f"Found {len(results)} relevant knowledge items")
    
    # Get statistics
    stats = framework.get_knowledge_statistics()
    print(f"Knowledge Graph Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())