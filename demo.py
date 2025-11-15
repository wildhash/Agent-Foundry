#!/usr/bin/env python
"""
Agent Foundry Demo Script
Demonstrates the complete self-evolving agent system
"""

import requests
import time
import json

API_BASE = "http://localhost:8000"


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(text):
    """Print formatted section"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print('─' * 70)


def demo():
    """Run complete Agent Foundry demonstration"""
    
    print_header("🔮 Agent Foundry Demo - Self-Evolving AI Agents")
    
    print("Agent Foundry is a self-evolving agent system that spawns specialized")
    print("agents to build, test, and deploy software autonomously.")
    print()
    print("Pipeline: Architect → Coder → Executor → Critic → Deployer")
    print("Each agent uses reflexion loops to continuously improve performance.")
    
    input("\nPress Enter to start the demo...")
    
    # 1. System Status
    print_section("1️⃣  System Status")
    
    response = requests.get(f"{API_BASE}/")
    app_info = response.json()
    print(f"✓ {app_info['name']} v{app_info['version']}")
    print(f"  {app_info['description']}")
    
    response = requests.get(f"{API_BASE}/health")
    print(f"✓ Health: {response.json()['status']}")
    
    time.sleep(1)
    
    # 2. Integration Status
    print_section("2️⃣  Integration Status")
    
    response = requests.get(f"{API_BASE}/api/metrics/integrations")
    integrations = response.json()
    
    print(f"⚡ Fastino TLM:")
    print(f"   Speed: {integrations['fastino_tlm']['speed_multiplier']}x faster inference")
    print(f"   Cache: {integrations['fastino_tlm']['cache_size']} items")
    
    print(f"\n🔧 LiquidMetal Raindrop:")
    print(f"   Auto-heal: {integrations['liquidmetal_raindrop']['auto_heal_enabled']}")
    print(f"   Sessions: {integrations['liquidmetal_raindrop']['total_sessions']}")
    
    print(f"\n🎨 Freepik API: Ready")
    print(f"🔐 Frontegg Auth: {integrations['frontegg_auth']['active_sessions']} sessions")
    print(f"🚀 Airia Deployment: {integrations['airia_deployment']['active_deployments']} active")
    
    time.sleep(2)
    input("\nPress Enter to create a pipeline...")
    
    # 3. Create Pipeline
    print_section("3️⃣  Creating Agent Pipeline")
    
    task = {
        "description": "Build a microservice for real-time chat with WebSocket support",
        "requirements": [
            "WebSocket server",
            "User authentication",
            "Message persistence",
            "Room management",
            "Real-time notifications"
        ],
        "language": "python"
    }
    
    print("Task: " + task['description'])
    print("\nRequirements:")
    for req in task['requirements']:
        print(f"  • {req}")
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline", json=task)
    pipeline = response.json()
    pipeline_id = pipeline['pipeline_id']
    
    print(f"\n✓ Pipeline created: {pipeline_id}")
    print(f"✓ Status: {pipeline['status']}")
    print("\nSpawning agents:")
    print("  🏗️  Architect Agent - System design")
    print("  💻 Coder Agent - Code generation")
    print("  ⚙️  Executor Agent - Run tests")
    print("  🔍 Critic Agent - Quality evaluation")
    print("  🚀 Deployer Agent - Production deployment")
    
    time.sleep(2)
    input("\nPress Enter to execute the pipeline...")
    
    # 4. Execute Pipeline
    print_section("4️⃣  Executing Pipeline (Reflexion Loops Active)")
    
    print("Each agent will:")
    print("  1. Execute their task")
    print("  2. Evaluate performance (0.0-1.0)")
    print("  3. Reflect on results")
    print("  4. Adjust strategy")
    print("  5. Repeat if score < 0.85\n")
    
    print("This may take a moment...\n")
    
    response = requests.post(f"{API_BASE}/api/agents/pipeline/{pipeline_id}/execute")
    result = response.json()
    
    # Display results for each agent
    print("Agent Results:")
    print()
    
    agents_emoji = {
        'architect': '🏗️',
        'coder': '💻',
        'executor': '⚙️',
        'critic': '🔍',
        'deployer': '🚀'
    }
    
    for agent_type, agent_result in result['results'].items():
        emoji = agents_emoji.get(agent_type, '🤖')
        score = agent_result.get('score', 0)
        loops = agent_result.get('loops_executed', 0)
        
        print(f"{emoji} {agent_type.capitalize()}")
        print(f"   Score: {score:.2%}")
        print(f"   Reflexion loops: {loops}")
        
        if score >= 0.85:
            print(f"   Status: ✅ Excellent performance!")
        elif score >= 0.75:
            print(f"   Status: ✓ Good performance")
        else:
            print(f"   Status: ⚠️  Needs improvement")
        print()
    
    overall_score = result['overall_score']
    print(f"Overall Pipeline Score: {overall_score:.2%}")
    
    if overall_score >= 0.85:
        print("✅ Pipeline PASSED - Agents will evolve!")
    else:
        print("⚠️  Pipeline needs improvement")
    
    time.sleep(2)
    input("\nPress Enter to view system metrics...")
    
    # 5. System Metrics
    print_section("5️⃣  System Metrics")
    
    response = requests.get(f"{API_BASE}/api/metrics/system")
    metrics = response.json()
    
    print(f"Total Agents: {metrics['total_agents']}")
    print(f"Active Pipelines: {metrics['active_pipelines']}")
    print(f"Completed Pipelines: {metrics['completed_pipelines']}")
    
    print(f"\nEvolution Tree:")
    print(f"  Nodes: {metrics['evolution_tree']['total_nodes']}")
    print(f"  Generations: {metrics['evolution_tree']['total_generations']}")
    print(f"  Avg Performance: {metrics['evolution_tree']['average_performance']:.2%}")
    print(f"  Best Performance: {metrics['evolution_tree']['best_performance']:.2%}")
    
    response = requests.get(f"{API_BASE}/api/metrics/performance")
    perf = response.json()
    
    print(f"\nPerformance Metrics:")
    print(f"  Average Score: {perf['average_score']:.2%}")
    print(f"  Best Score: {perf['best_score']:.2%}")
    print(f"  Total Executions: {perf['total_executions']}")
    print(f"  Agents Tracked: {perf['agents_tracked']}")
    
    time.sleep(2)
    input("\nPress Enter to view evolution tree...")
    
    # 6. Evolution Tree
    print_section("6️⃣  Evolution Tree")
    
    response = requests.get(f"{API_BASE}/api/evolution/tree")
    tree = response.json()
    
    print(f"Evolution Tree Structure:")
    print(f"  Total Nodes: {tree['total_nodes']}")
    print(f"  Total Edges: {len(tree['edges'])}")
    print(f"  Generations: {tree['total_generations']}")
    
    response = requests.get(f"{API_BASE}/api/evolution/best-performers?top_n=5")
    performers = response.json()['top_performers']
    
    print(f"\n🏆 Top Performers:")
    for i, performer in enumerate(performers[:5], 1):
        print(f"  {i}. {performer['node_id']}")
        print(f"     Score: {performer['performance_score']:.2%}")
        print(f"     Generation: {performer['generation']}")
    
    time.sleep(2)
    input("\nPress Enter to simulate deployment...")
    
    # 7. Deployment
    print_section("7️⃣  Enterprise Deployment (Airia)")
    
    if overall_score >= 0.75:
        best_agent = result['agents']['deployer']['agent_id']
        
        print(f"Deploying best performing agent: {best_agent}")
        
        deploy_config = {
            "agent_id": best_agent,
            "environment": "production",
            "replicas": 3
        }
        
        response = requests.post(f"{API_BASE}/api/deployment/deploy", json=deploy_config)
        deployment = response.json()
        
        print(f"\n✅ Deployment Successful!")
        print(f"  Deployment ID: {deployment['deployment_id']}")
        print(f"  Endpoint: {deployment['endpoint']}")
        print(f"  Replicas: {deployment['replicas']}")
        print(f"  Health: {deployment['health_check']}")
        
        print(f"\n📊 Metrics:")
        metrics = deployment['metrics']
        print(f"  CPU Usage: {metrics['cpu_usage']}%")
        print(f"  Memory: {metrics['memory_usage'] / 1024 / 1024:.1f} MB")
        print(f"  Requests/sec: {metrics['requests_per_second']}")
    else:
        print("⚠️  Score too low for production deployment")
        print("Agent will continue learning through reflexion loops")
    
    # Summary
    print_section("8️⃣  Demo Complete!")
    
    print("✅ Agent Foundry successfully demonstrated:")
    print()
    print("  🏗️  Agent Pipeline: Architect → Coder → Executor → Critic → Deployer")
    print("  🔄 Reflexion Loops: Execute → Evaluate → Reflect → Improve")
    print("  🧠 Meta-Learning: Learn from past experiences")
    print("  🌳 Evolution: High performers spawn improved children")
    print("  ⚡ Fastino TLM: 99x faster inference")
    print("  🔧 LiquidMetal: Self-healing code")
    print("  🚀 Airia: Enterprise deployment")
    print()
    print("Dashboard available at: http://localhost:3000")
    print("API Documentation: http://localhost:8000/docs")
    print()
    print("Thank you for trying Agent Foundry! 🔮")
    print()


if __name__ == "__main__":
    try:
        demo()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server")
        print("Please ensure the backend is running:")
        print("  cd backend && uvicorn main:app --reload")
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
