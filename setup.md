Windows
│
├── VS Code
├── Python 3.11/3.12
├── Git
├── Docker Desktop
│
├── Ollama
│   └── Local LLM
│
└── Project
    ├── FastAPI
    ├── LangGraph
    ├── SQLAlchemy
    └── FalkorDB



Project structure

agentic-text2sql/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── agents/
│   │   ├── planner.py
│   │   ├── schema_agent.py
│   │   ├── sql_generator.py
│   │   ├── sql_validator.py
│   │   ├── executor.py
│   │   └── analyst.py
│   │
│   ├── graph/
│   │   ├── client.py
│   │   ├── schema_loader.py
│   │   ├── semantic_search.py
│   │   └── queries.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── metadata.py
│   │   └── executor.py
│   │
│   ├── llm/
│   │   ├── ollama.py
│   │   └── prompts.py
│   │
│   ├── workflow/
│   │   ├── state.py
│   │   └── graph.py
│   │
│   └── utils/
│       ├── logger.py
│       └── config.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── data/
│   └── chinook.db
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md