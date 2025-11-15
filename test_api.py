#!/usr/bin/env python
"""
Test script for Agent Foundry API
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"✓ Health: {response.json()}")
    return response.status_code == 200


def test_root():
    """Test root endpoint"""
    print("\nTesting root endpoint...")
    response = requests.get(f"{API_BASE}/")
    data = response.json()
    print(f"✓ App: {data['name']} v{data['version']}")
    return response.status_code == 200


def test_create_pipeline():
    """Test pipeline creation"""
    print("\nTesting pipeline creation...")
    payload = {
        "description": "Build a REST API for user management",
        "requirements": [
            "CRUD operations",
            "JWT authentication",
            "PostgreSQL database"
        ],
        "language": "python"
    }
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline", json=payload)
    data = response.json()
    print(f"✓ Created pipeline: {data['pipeline_id']}")
    return data['pipeline_id']


def test_execute_pipeline(pipeline_id):
    """Test pipeline execution"""
    print(f"\nTesting pipeline execution for {pipeline_id}...")
    print("This may take a moment...")
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline/{pipeline_id}/execute")
    data = response.json()
    
    print(f"✓ Pipeline Status: {data['status']}")
    print(f"✓ Overall Score: {data['overall_score']:.2%}")
    print(f"✓ Agents: {', '.join(data['agents'].keys())}")
    
    return data


def test_get_pipeline_status(pipeline_id):
    """Test getting pipeline status"""
    print(f"\nTesting get pipeline status...")
    
    response = requests.get(f"{API_BASE}/api/agents/pipeline/{pipeline_id}")
    data = response.json()
    
    print(f"✓ Pipeline: {data['pipeline_id']}")
    print(f"✓ Status: {data['status']}")
    
    return data


def test_list_agents():
    """Test listing agents"""
    print("\nTesting list agents...")
    
    response = requests.get(f"{API_BASE}/api/agents/agents")
    data = response.json()
    
    print(f"✓ Total agents: {len(data['agents'])}")
    for agent in data['agents'][:3]:  # Show first 3
        print(f"  - {agent['agent_id']} ({agent['agent_type']})")
    
    return data


def test_metrics():
    """Test metrics endpoints"""
    print("\nTesting metrics endpoints...")
    
    # System metrics
    response = requests.get(f"{API_BASE}/api/metrics/system")
    data = response.json()
    print(f"✓ System Metrics:")
    print(f"  - Total agents: {data['total_agents']}")
    print(f"  - Active pipelines: {data['active_pipelines']}")
    print(f"  - Completed pipelines: {data['completed_pipelines']}")
    
    # Performance metrics
    response = requests.get(f"{API_BASE}/api/metrics/performance")
    data = response.json()
    print(f"✓ Performance Metrics:")
    print(f"  - Average score: {data['average_score']:.2%}")
    print(f"  - Total executions: {data['total_executions']}")
    
    # Integration metrics
    response = requests.get(f"{API_BASE}/api/metrics/integrations")
    data = response.json()
    print(f"✓ Integration Metrics:")
    print(f"  - Fastino TLM cache: {data['fastino_tlm']['cache_size']} items")
    print(f"  - Fastino speed: {data['fastino_tlm']['speed_multiplier']}x")
    print(f"  - Raindrop sessions: {data['liquidmetal_raindrop']['total_sessions']}")
    print(f"  - Issues fixed: {data['liquidmetal_raindrop']['total_issues_fixed']}")
    
    return True


def test_evolution_tree():
    """Test evolution tree endpoints"""
    print("\nTesting evolution tree endpoints...")
    
    # Get tree
    response = requests.get(f"{API_BASE}/api/evolution/tree")
    data = response.json()
    print(f"✓ Evolution Tree:")
    print(f"  - Total nodes: {data['total_nodes']}")
    print(f"  - Total generations: {data['total_generations']}")
    
    # Get stats
    response = requests.get(f"{API_BASE}/api/evolution/tree/stats")
    data = response.json()
    print(f"✓ Tree Stats:")
    print(f"  - Average performance: {data['average_performance']:.2%}")
    print(f"  - Best performance: {data['best_performance']:.2%}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent Foundry API Test Suite")
    print("=" * 60)
    
    try:
        # Basic tests
        assert test_health(), "Health check failed"
        assert test_root(), "Root endpoint failed"
        
        # Pipeline tests
        pipeline_id = test_create_pipeline()
        time.sleep(1)
        
        result = test_execute_pipeline(pipeline_id)
        time.sleep(1)
        
        test_get_pipeline_status(pipeline_id)
        time.sleep(1)
        
        # Agent tests
        test_list_agents()
        time.sleep(1)
        
        # Metrics tests
        test_metrics()
        time.sleep(1)
        
        # Evolution tests
        test_evolution_tree()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
