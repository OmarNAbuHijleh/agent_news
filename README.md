# README

## Purpose
This repository contains the code for a news research agent. Given a topic, it will:
- investigate across multiple sources
- identify the factual core
- detect disagreements
- reconstruct the timeline
- explain what is known vs. what is uncertain

## Structure [in progress]
### Agents involved:
1. Research Planner
2. Research Agent
3. Evidence/Fact Checking Agent
4. Synthesis Agent (Produces the final report)

### Under the Hood
Chain of thought will be exposed and visible for all to see. Therefore, users can see:
- tool calls
- searches 
- sources selected
- evidences 
- agent decisions
- confidence
- execution time

### Tools I intent to use:
- python and its accompanying libraries (see "pyproject.toml")
- AWS lambda (for API), DynamoDB/ElastiCache, Cloudwatch
- LLM API (provider tbd)
- search/news API


### Cost Saving
I'm not made of money, so I'd like to keep as much of what I have as possible. I'm going to follow this architecture so that I can cache the redundant searches:
```text
User
  │
  ▼
Query Normalizer
  │
  ▼
Cache / Database
/          \
HIT            MISS
│               │
▼               ▼
Return result     Run agents
           │
           ▼
        Cache
```

## Features
- Trending Investigations: This is going to be a page that tracks what is currently trending and will fire an update for those topics occasionally.
- Ask the Investigation: Following the synthesizing of a report, we'll give users the ability to ask follow up questions and discuss the results.
  - For example:
    1. User: "Why does the report say NVIDIA's position is strengthening?"
    2. The system performs RAG over the investigation's evidence and responds: "The conclusion is primarily based on sources A, B and C..."
    3. "What evidence contradicts that?"
    4. The system retrieves the contradictory evidence and provides it


## Project File Structure
```
root_dir/
├── pyproject.toml
├── uv.lock
├── README.md
├── CHANGELOG.md
├── TODO.md
├── config.py                       # Environment/configuration (GEMINI_API_KEY, MAX_RESEARCH_ITERATIONS)
├── .env
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # Entry point
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent_type_enum.py      # AgentType enum, tags each research step
│   │   ├── research_step.py        # ResearchStep dataclass (agent_type + content)
│   │   ├── research_utils.py       # Flattens ResearchStep history into model input
│   │   ├── retry.py                # Rate-limit retry/backoff wrapper for API calls
│   │   ├── research_orchestrator.py# ResearchOrchestrator: owns the shared client, runs the plan/research/fact-check/synthesize loop
│   │   ├── research_agent.py
│   │   ├── fact_checking_agent.py
│   │   ├── synthesis_agent.py
│   │   └── agent_tools/            # Custom tools for the research agent (planned, not yet implemented)
│   │
│   ├── api/
│   │   └── __init__.py             # API routes (planned, not yet implemented)
│   │
│   └── services/
│       └── __init__.py             # External APIs, DB, etc. (planned, not yet implemented)
│
└── test/                           # Unit tests (planned, not yet implemented)
```
