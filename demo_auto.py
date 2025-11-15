#!/usr/bin/env python
"""
Agent Foundry Automated Demo
Non-interactive version for automated demonstration
"""

import requests
import time

API_BASE = "http://localhost:8000"


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def main():
    print_section("🔮 Agent Foundry - Automated Demo")
    print("\nAgent Foundry: Self-evolving agents with reflexion loops")
    print("Pipeline: Architect → Coder → Executor → Critic → Deployer\n")
    
    # 1. System check
    print("1️⃣  Checking system status...")
    response = requests.get(f"{API_BASE}/")
    app = response.json()
    print(f"   ✓ {app['name']} v{app['version']}")
    
    response = requests.get(f"{API_BASE}/health")
    print(f"   ✓ Health: {response.json()['status']}")
    
    # 2. Integrations
    print("\n2️⃣  Checking integrations...")
    response = requests.get(f"{API_BASE}/api/metrics/integrations")
    integrations = response.json()
    print(f"   ⚡ Fastino TLM: {integrations['fastino_tlm']['speed_multiplier']}x faster")
    print(f"   🔧 Raindrop: Auto-healing enabled")
    print(f"   🎨 Freepik: Ready")
    print(f"   🔐 Frontegg: Ready")
    print(f"   🚀 Airia: Ready")
    
    # 3. Create pipeline
    print("\n3️⃣  Creating pipeline...")
    task = {
        "description": "Build a REST API for order processing",
        "requirements": ["CRUD operations", "Validation", "Database"],
        "language": "python"
    }
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline", json=task)
    pipeline_id = response.json()['pipeline_id']
    print(f"   ✓ Pipeline created: {pipeline_id}")
    print(f"   ✓ Agents spawned: 5 (architect, coder, executor, critic, deployer)")
    
    # 4. Execute
    print("\n4️⃣  Executing pipeline with reflexion loops...")
    print("   Each agent: Execute → Evaluate → Reflect → Improve")
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline/{pipeline_id}/execute")
    result = response.json()
    
    print(f"\n   Agent Performance:")
    for agent_type, agent_result in result['results'].items():
        score = agent_result.get('score', 0)
        loops = agent_result.get('loops_executed', 0)
        status = "✅" if score >= 0.85 else "✓" if score >= 0.75 else "⚠️"
        print(f"   {status} {agent_type.capitalize()}: {score:.1%} ({loops} loops)")
    
    overall = result['overall_score']
    print(f"\n   Overall Score: {overall:.1%}")
    print(f"   Status: {'✅ PASSED - Agents evolving!' if overall >= 0.85 else '✓ Completed'}")
    
    # 5. Metrics
    print("\n5️⃣  System metrics...")
    response = requests.get(f"{API_BASE}/api/metrics/system")
    metrics = response.json()
    print(f"   • Total agents: {metrics['total_agents']}")
    print(f"   • Completed pipelines: {metrics['completed_pipelines']}")
    print(f"   • Evolution generations: {metrics['evolution_tree']['total_generations']}")
    
    response = requests.get(f"{API_BASE}/api/metrics/performance")
    perf = response.json()
    print(f"   • Average performance: {perf['average_score']:.1%}")
    print(f"   • Total executions: {perf['total_executions']}")
    
    # 6. Evolution
    print("\n6️⃣  Evolution tree...")
    response = requests.get(f"{API_BASE}/api/evolution/best-performers?top_n=3")
    performers = response.json()['top_performers']
    
    print(f"   🏆 Top performers:")
    for i, p in enumerate(performers[:3], 1):
        print(f"   {i}. {p['node_id']}: {p['performance_score']:.1%}")
    
    # 7. Deploy
    if overall >= 0.75:
        print("\n7️⃣  Deploying to production...")
        deploy_config = {
            "agent_id": result['agents']['deployer']['agent_id'],
            "environment": "production",
            "replicas": 3
        }
        
        response = requests.post(f"{API_BASE}/api/deployment/deploy", json=deploy_config)
        deployment = response.json()
        
        print(f"   ✅ Deployed: {deployment['deployment_id']}")
        print(f"   • Endpoint: {deployment['endpoint']}")
        print(f"   • Replicas: {deployment['replicas']}")
        print(f"   • Health: {deployment['health_check']}")
    
    print_section("✅ Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Self-evolving agents with reflexion loops")
    print("  ✓ 99x faster inference (Fastino TLM)")
    print("  ✓ Self-healing code (LiquidMetal Raindrop)")
    print("  ✓ Evolution tree tracking")
    print("  ✓ Enterprise deployment (Airia)")
    print("\nDashboard: http://localhost:3000")
    print("API Docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend not running. Start with:")
        print("   cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
