# Agent Foundry Architecture

## System Overview

Agent Foundry is a self-evolving agent system built on the principle of continuous improvement through reflexion loops and meta-learning.

## Core Components

### 1. Agent System

#### Base Agent (`base_agent.py`)
The foundation for all specialized agents with:
- **Reflexion Loop**: Execute → Evaluate → Reflect → Adjust
- **Performance Tracking**: Score each execution (0.0-1.0)
- **Memory System**: Store experiences and learn from them
- **Meta-Learning**: Analyze patterns in successful/unsuccessful attempts
- **Evolution**: Spawn improved child agents when performance exceeds threshold

#### Specialized Agents

**Architect Agent**
- Designs system architecture
- Uses Fastino TLM for fast generation
- Evaluates based on completeness, modularity, scalability
- Adjusts design patterns based on feedback

**Coder Agent**
- Generates code from architecture
- Integrates LiquidMetal Raindrop for self-healing
- Evaluates code quality and structure
- Adjusts coding style based on performance

**Executor Agent**
- Runs code in sandboxed environment
- Tracks execution metrics (time, memory, exit code)
- Evaluates success rate and performance
- Optimizes execution strategy

**Critic Agent**
- Evaluates work from other agents
- Provides constructive feedback
- Calculates overall quality score
- Determines if work passes quality threshold

**Deployer Agent**
- Handles production deployment
- Uses Airia for enterprise deployment
- Monitors health and metrics
- Adjusts deployment strategy (rolling, blue-green)

### 2. Orchestrator (`orchestrator.py`)

Implements **Campfire Patterns** for agent coordination:

```python
Pipeline Flow:
Architect → Coder → Executor → Critic → Deployer

For each stage:
1. Agent performs task with reflexion loops
2. Performance evaluated and scored
3. Results passed to next stage
4. Overall pipeline score calculated
```

Features:
- Pipeline management (create, execute, monitor)
- Agent spawning and registration
- Evolution tree updates
- Performance aggregation

### 3. Integration Layer

#### Fastino TLM (`integrations/fastino.py`)
- 99x faster inference (0.01s vs 1s)
- Intelligent caching
- Batch processing support
- Mock responses for development

#### LiquidMetal Raindrop (`integrations/raindrop.py`)
- Automatic issue detection
- Self-healing code fixes
- Multiple healing attempts
- Validation and verification

#### Freepik API (`integrations/__init__.py`)
- AI-generated visuals
- Agent avatars
- Evolution tree visualizations
- Dashboard graphics

#### Frontegg Auth (`integrations/__init__.py`)
- Multi-tenant authentication
- Session management
- Token validation
- Tenant creation

#### Airia Deployment (`integrations/__init__.py`)
- Enterprise deployment
- Scaling and monitoring
- Health checks
- Metrics collection

### 4. Evolution System (`models/evolution.py`)

Uses **NetworkX** for graph operations:

```python
Evolution Tree Structure:
- Nodes: Agent instances with performance scores
- Edges: Parent-child relationships
- Generations: Levels in the tree
```

Features:
- Lineage tracking
- Performance analysis
- Best performers identification
- Improvement rate calculations

### 5. API Layer

**FastAPI** with async support:
- RESTful endpoints
- OpenAPI documentation
- CORS middleware
- Async request handling

Routes:
- `/api/agents/*` - Agent management
- `/api/evolution/*` - Evolution tracking
- `/api/metrics/*` - System metrics
- `/api/deployment/*` - Deployment management

## Data Flow

### 1. Pipeline Creation
```
User Request
    ↓
FastAPI Endpoint
    ↓
Orchestrator.create_pipeline()
    ↓
Spawn 5 specialized agents
    ↓
Register in orchestrator
    ↓
Return pipeline_id
```

### 2. Pipeline Execution
```
Execute Request
    ↓
Orchestrator.execute_pipeline()
    ↓
Sequential Agent Execution:
    1. Architect (design)
    2. Coder (generate code)
    3. Executor (run code)
    4. Critic (evaluate)
    5. Deployer (deploy if passed)
    ↓
Each agent runs reflexion loop:
    - Execute task
    - Evaluate performance
    - Reflect on results
    - Adjust strategy
    - Repeat if score < threshold
    ↓
Calculate overall pipeline score
    ↓
Update evolution tree
    ↓
Spawn children if score >= 0.85
    ↓
Return results
```

### 3. Reflexion Loop Detail
```
Agent.reflexion_loop(task)
    ↓
Loop (max 5 times):
    ├─ Execute Task
    │   └─ Agent-specific logic
    ├─ Evaluate Performance
    │   └─ Score 0.0-1.0
    ├─ Store in Memory
    │   └─ Task, Action, Result, Score
    ├─ Check Threshold
    │   └─ If >= 0.85, stop
    ├─ Reflect & Adjust
    │   ├─ Analyze trend
    │   ├─ Adjust strategy
    │   └─ Meta-learn from memory
    └─ Continue to next loop
    ↓
Return best result
```

### 4. Evolution Process
```
Pipeline Score >= 0.85
    ↓
For each agent in pipeline:
    ├─ Spawn child agent
    │   └─ child_id = parent_id + "_gen{N}"
    ├─ Update evolution tree
    │   ├─ Add node (child)
    │   └─ Add edge (parent → child)
    └─ Register new agent
    ↓
Next execution uses evolved agents
```

## Performance Optimization

### 1. Fastino TLM Caching
```python
# First call: Full inference
response = fastino.generate(prompt)  # 0.01s

# Subsequent calls: Cached
response = fastino.generate(prompt)  # <0.001s
```

### 2. Async Operations
All I/O operations are async:
- API requests
- Agent execution
- Database operations
- File operations

### 3. Parallel Agent Execution
Within reflexion loops, independent operations run in parallel:
```python
# Multiple evaluations
results = await asyncio.gather(
    agent1.evaluate(),
    agent2.evaluate(),
    agent3.evaluate()
)
```

## Scalability

### Horizontal Scaling
- FastAPI workers (4+ recommended)
- Load balancing across instances
- Shared Redis for caching
- PostgreSQL for persistence

### Vertical Scaling
- Increase reflexion loop iterations
- Batch processing with Fastino
- Memory-based learning caching

## Security Considerations

### 1. Code Execution
- Sandboxed environments for Executor
- Resource limits (CPU, memory, time)
- Input validation and sanitization

### 2. Authentication
- Frontegg multi-tenant auth
- JWT token validation
- Role-based access control

### 3. Data Protection
- Environment variable for secrets
- Encryption at rest and in transit
- Audit logging

## Monitoring & Observability

### Metrics Collection
- System metrics (agents, pipelines)
- Performance metrics (scores, executions)
- Integration metrics (cache, healing)
- Reflexion metrics (loops, improvements)

### Logging
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Correlation IDs for tracing

### Health Checks
- `/health` endpoint
- Component status checks
- Resource availability

## Future Enhancements

1. **Distributed Agents**: Run agents across multiple nodes
2. **Advanced Learning**: Reinforcement learning for strategy optimization
3. **Agent Communication**: Direct agent-to-agent messaging
4. **Version Control**: Git integration for code generation
5. **Testing Framework**: Automated test generation and execution
6. **Production Ready**: Database persistence, real sandboxing, production Fastino integration
