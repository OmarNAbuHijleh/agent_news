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

## Features
- Trending Investigations: This is going to be a page that tracks what is currently trending and will fire an update for those topics occasionally.
- Ask the Investigation: Following the synthesizing of a report, we'll give users the ability to ask follow up questions and discuss the results.
  - For example:
    1. User: "Why does the report say NVIDIA's position is strengthening?"
    2. The system performs RAG over the investigation's evidence and responds: "The conclusion is primarily based on sources A, B and C..."
    3. "What evidence contradicts that?"
    4. The system retrieves the contradictory evidence and provides it


## Project File Structure
root_dir/
├── pyproject.toml
├── README.md
├── .env
├── .gitignore
│
├── src/
│   └── agentic_news/
│       ├── __init__.py
│       │
│       ├── main.py                 # FastAPI application entry point
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       └── agents.py       # API endpoints
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py             # Shared agent abstractions
│       │   ├── research_agent.py
│       │   └── ...
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   └── ...                 # External APIs, DB, etc.
│       │
│       └── config.py               # Environment/configuration
│
└── tests/
    ├── __init__.py
    ├── api/
    │   └── test_agents.py
    ├── agents/
    │   └── test_research_agent.py
    └── conftest.py
