"""
Evolution Tree model with database persistence
"""

from typing import Dict, Any, List, Optional
import networkx as nx
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import EvolutionNode as EvolutionNodeDB
import logging

logger = logging.getLogger(__name__)


class EvolutionTree:
    """
    Tracks agent evolution across generations
    Uses NetworkX for in-memory operations, SQLAlchemy for persistence
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.graph = nx.DiGraph()
        self.generations: Dict[int, List[str]] = {}
        self.db_session = db_session

    def add_node(
        self,
        node_id: str,
        generation: int,
        performance_score: float,
        agent_type: str = "unknown",
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a node to the evolution tree and persist to database"""
        timestamp = datetime.now()

        # Add to in-memory graph
        self.graph.add_node(
            node_id,
            generation=generation,
            performance_score=performance_score,
            agent_type=agent_type,
            parent_id=parent_id,
            metadata=metadata or {},
            created_at=timestamp.isoformat(),
        )

        if generation not in self.generations:
            self.generations[generation] = []
        self.generations[generation].append(node_id)

        # Add edge if parent exists
        if parent_id and parent_id in self.graph:
            self.graph.add_edge(parent_id, node_id)

        # Persist to database if session available
        if self.db_session:
            self._persist_node(
                node_id,
                generation,
                performance_score,
                agent_type,
                parent_id,
                metadata,
                timestamp,
            )

    def _persist_node(
        self,
        node_id: str,
        generation: int,
        performance_score: float,
        agent_type: str,
        parent_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
        timestamp: datetime,
    ):
        """Persist node to database"""
        try:
            db_node = EvolutionNodeDB(
                id=node_id,
                parent_id=parent_id,
                agent_type=agent_type,
                generation=generation,
                performance_score=performance_score,
                extra_data=metadata,
                created_at=timestamp,
            )
            self.db_session.add(db_node)
            self.db_session.commit()
            logger.debug(f"Persisted evolution node: {node_id}")
        except Exception as e:
            logger.error(f"Failed to persist evolution node: {e}")
            self.db_session.rollback()

    def load_from_database(self):
        """Load existing nodes from database"""
        if not self.db_session:
            logger.warning("No database session, cannot load evolution tree")
            return

        try:
            nodes = self.db_session.query(EvolutionNodeDB).all()

            for node in nodes:
                self.graph.add_node(
                    node.id,
                    generation=node.generation,
                    performance_score=node.performance_score,
                    agent_type=node.agent_type,
                    parent_id=node.parent_id,
                    metadata=node.extra_data or {},
                    created_at=node.created_at.isoformat()
                    if node.created_at
                    else None,
                )

                if node.generation not in self.generations:
                    self.generations[node.generation] = []
                self.generations[node.generation].append(node.id)

                if node.parent_id and node.parent_id in self.graph:
                    self.graph.add_edge(node.parent_id, node.id)

            logger.info(f"Loaded {len(nodes)} evolution nodes from database")

        except Exception as e:
            logger.error(f"Failed to load evolution tree: {e}")

    def add_edge(self, parent_id: str, child_id: str):
        """Add parent-child relationship"""
        if parent_id in self.graph and child_id in self.graph:
            self.graph.add_edge(parent_id, child_id)

    def get_lineage(self, node_id: str) -> List[str]:
        """Get full lineage (ancestors) of a node"""
        if node_id not in self.graph:
            return []

        ancestors = []
        for ancestor in nx.ancestors(self.graph, node_id):
            ancestors.append(ancestor)

        return sorted(ancestors)

    def get_descendants(self, node_id: str) -> List[str]:
        """Get all descendants of a node"""
        if node_id not in self.graph:
            return []

        descendants = []
        for descendant in nx.descendants(self.graph, node_id):
            descendants.append(descendant)

        return descendants

    def get_generation(self, generation_num: int) -> List[Dict[str, Any]]:
        """Get all nodes in a specific generation"""
        if generation_num not in self.generations:
            return []

        nodes = []
        for node_id in self.generations[generation_num]:
            node_data = self.graph.nodes[node_id]
            nodes.append({"node_id": node_id, **node_data})

        return nodes

    def get_best_performers(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top performing nodes"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append(
                {
                    "node_id": node_id,
                    "performance_score": data.get("performance_score", 0.0),
                    "generation": data.get("generation", 0),
                    "metadata": data.get("metadata", {}),
                }
            )

        # Sort by performance score
        nodes.sort(key=lambda x: x["performance_score"], reverse=True)

        return nodes[:top_n]

    def get_evolution_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Get evolution path between two nodes"""
        if start_id not in self.graph or end_id not in self.graph:
            return None

        try:
            return nx.shortest_path(self.graph, start_id, end_id)
        except nx.NetworkXNoPath:
            return None

    def calculate_improvement_rate(self, node_id: str) -> float:
        """Calculate performance improvement rate for a lineage"""
        lineage = self.get_lineage(node_id)
        if not lineage:
            return 0.0

        # Get performance scores
        scores = []
        for ancestor_id in lineage:
            score = self.graph.nodes[ancestor_id].get("performance_score", 0.0)
            scores.append(score)

        if len(scores) < 2:
            return 0.0

        # Calculate improvement rate
        initial_score = scores[0]
        final_score = scores[-1]

        if initial_score == 0:
            return 0.0

        return (final_score - initial_score) / initial_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary representation"""
        nodes = []
        edges = []

        for node_id, data in self.graph.nodes(data=True):
            nodes.append(
                {
                    "id": node_id,
                    "generation": data.get("generation", 0),
                    "performance_score": data.get("performance_score", 0.0),
                    "metadata": data.get("metadata", {}),
                    "created_at": data.get("created_at"),
                }
            )

        for parent, child in self.graph.edges():
            edges.append({"parent": parent, "child": child})

        return {
            "nodes": nodes,
            "edges": edges,
            "total_generations": len(self.generations),
            "total_nodes": len(nodes),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get tree statistics"""
        scores = [data.get("performance_score", 0.0) for _, data in self.graph.nodes(data=True)]

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "total_generations": len(self.generations),
            "average_performance": sum(scores) / len(scores) if scores else 0.0,
            "best_performance": max(scores) if scores else 0.0,
        }
