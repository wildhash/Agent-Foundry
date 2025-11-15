"""
Evolution Tree model for tracking agent lineage and performance
"""

from typing import Dict, Any, List, Optional
import networkx as nx
from datetime import datetime


class EvolutionTree:
    """
    Tracks agent evolution across generations
    Uses NetworkX for graph operations
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.generations: Dict[int, List[str]] = {}
        
    def add_node(
        self,
        node_id: str,
        generation: int,
        performance_score: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a node to the evolution tree"""
        self.graph.add_node(
            node_id,
            generation=generation,
            performance_score=performance_score,
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )
        
        if generation not in self.generations:
            self.generations[generation] = []
        self.generations[generation].append(node_id)
        
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
            nodes.append({
                "node_id": node_id,
                **node_data
            })
            
        return nodes
    
    def get_best_performers(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top performing nodes"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "node_id": node_id,
                "performance_score": data.get("performance_score", 0.0),
                "generation": data.get("generation", 0),
                "metadata": data.get("metadata", {})
            })
        
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
            nodes.append({
                "id": node_id,
                "generation": data.get("generation", 0),
                "performance_score": data.get("performance_score", 0.0),
                "metadata": data.get("metadata", {}),
                "created_at": data.get("created_at")
            })
        
        for parent, child in self.graph.edges():
            edges.append({
                "parent": parent,
                "child": child
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "total_generations": len(self.generations),
            "total_nodes": len(nodes)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tree statistics"""
        scores = [
            data.get("performance_score", 0.0)
            for _, data in self.graph.nodes(data=True)
        ]
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "total_generations": len(self.generations),
            "average_performance": sum(scores) / len(scores) if scores else 0.0,
            "best_performance": max(scores) if scores else 0.0
        }
