# Agent Foundry Examples

## Example 1: Simple Pipeline

Create and execute a basic agent pipeline:

```python
import requests

API_BASE = "http://localhost:8000"

# Create pipeline
response = requests.post(f"{API_BASE}/api/agents/pipeline", json={
    "description": "Build a REST API for user management",
    "requirements": [
        "CRUD operations",
        "JWT authentication",
        "PostgreSQL database"
    ],
    "language": "python"
})

pipeline_id = response.json()['pipeline_id']
print(f"Created: {pipeline_id}")

# Execute pipeline
response = requests.post(f"{API_BASE}/api/agents/pipeline/{pipeline_id}/execute")
result = response.json()
print(f"Score: {result['overall_score']:.2%}")
```

## Example 2: Monitor Agent Performance

Track individual agent performance:

```python
import requests

API_BASE = "http://localhost:8000"

# List all agents
response = requests.get(f"{API_BASE}/api/agents/agents")
agents = response.json()['agents']

for agent in agents:
    print(f"\n{agent['agent_id']} ({agent['agent_type']})")
    
    # Get performance details
    perf = agent['performance_summary']
    print(f"  Average Score: {perf['average_score']:.2%}")
    print(f"  Best Score: {perf['best_score']:.2%}")
    print(f"  Executions: {perf['total_executions']}")
    print(f"  Generation: {perf['current_generation']}")
```

## Example 3: Track Evolution

Monitor agent evolution over time:

```python
import requests

API_BASE = "http://localhost:8000"

# Get evolution tree
response = requests.get(f"{API_BASE}/api/evolution/tree")
tree = response.json()

print(f"Generations: {tree['total_generations']}")
print(f"Total Nodes: {tree['total_nodes']}")

# Get best performers
response = requests.get(f"{API_BASE}/api/evolution/best-performers?top_n=5")
performers = response.json()['top_performers']

print("\nTop Performers:")
for i, p in enumerate(performers, 1):
    print(f"{i}. {p['node_id']}: {p['performance_score']:.2%}")
```

## Example 4: Deploy an Agent

Deploy an agent using Airia:

```python
import requests

API_BASE = "http://localhost:8000"

# Deploy agent
response = requests.post(f"{API_BASE}/api/deployment/deploy", json={
    "agent_id": "pipeline_0_architect",
    "environment": "production",
    "replicas": 3
})

deployment = response.json()
print(f"Deployed: {deployment['deployment_id']}")
print(f"Endpoint: {deployment['endpoint']}")
print(f"Health: {deployment['health_check']}")

# Get metrics
deployment_id = deployment['deployment_id']
response = requests.get(f"{API_BASE}/api/deployment/deployments/{deployment_id}/metrics")
metrics = response.json()

print(f"CPU Usage: {metrics['cpu_usage']}%")
print(f"Memory: {metrics['memory_usage']} bytes")
print(f"RPS: {metrics['requests_per_second']}")
```

## Example 5: Integration Metrics

Monitor all integrations:

```python
import requests

API_BASE = "http://localhost:8000"

response = requests.get(f"{API_BASE}/api/metrics/integrations")
integrations = response.json()

# Fastino TLM
fastino = integrations['fastino_tlm']
print(f"Fastino TLM:")
print(f"  Speed Multiplier: {fastino['speed_multiplier']}x")
print(f"  Cache Size: {fastino['cache_size']}")

# LiquidMetal Raindrop
raindrop = integrations['liquidmetal_raindrop']
print(f"\nLiquidMetal Raindrop:")
print(f"  Sessions: {raindrop['total_sessions']}")
print(f"  Issues Fixed: {raindrop['total_issues_fixed']}")
print(f"  Avg Issues/Session: {raindrop['average_issues_per_session']:.1f}")

# Airia Deployment
airia = integrations['airia_deployment']
print(f"\nAiria Deployment:")
print(f"  Total Deployments: {airia['total_deployments']}")
print(f"  Active: {airia['active_deployments']}")
```

## Example 6: Complete Workflow

Full workflow from creation to deployment:

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. Create pipeline
print("1. Creating pipeline...")
response = requests.post(f"{API_BASE}/api/agents/pipeline", json={
    "description": "Build a microservice for order processing",
    "requirements": [
        "Event-driven architecture",
        "Message queue integration",
        "Database transactions",
        "Error handling"
    ],
    "language": "python"
})
pipeline_id = response.json()['pipeline_id']
print(f"   Created: {pipeline_id}")

# 2. Execute pipeline
print("\n2. Executing pipeline...")
response = requests.post(f"{API_BASE}/api/agents/pipeline/{pipeline_id}/execute")
result = response.json()
print(f"   Score: {result['overall_score']:.2%}")

# 3. Check if it passed critique
if result['results']['critic']['result']['passed']:
    print("\n3. Critique passed! Deploying...")
    
    # Get the best performing agent
    response = requests.get(f"{API_BASE}/api/evolution/best-performers?top_n=1")
    best_agent = response.json()['top_performers'][0]
    
    # Deploy
    response = requests.post(f"{API_BASE}/api/deployment/deploy", json={
        "agent_id": best_agent['node_id'],
        "environment": "production",
        "replicas": 3
    })
    deployment = response.json()
    print(f"   Deployed: {deployment['endpoint']}")
else:
    print("\n3. Critique failed, needs improvement")

# 4. Check evolution
print("\n4. Checking evolution...")
response = requests.get(f"{API_BASE}/api/evolution/tree/stats")
stats = response.json()
print(f"   Generations: {stats['total_generations']}")
print(f"   Best Performance: {stats['best_performance']:.2%}")
```

## Run Examples

```bash
# Start the backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, run examples
python examples/example1.py
python examples/example2.py
# etc...
```
