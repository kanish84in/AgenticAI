                        ┌─────────────────────────┐
                        │      HTML Frontend       │
                        │                         │
                        │  Natural Language Query │
                        │  SQL / Results / Trace  │
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │        FastAPI          │
                        │       REST APIs         │
                        └────────────┬────────────┘
                                     │
                                     ▼
                 ┌────────────────────────────────────┐
                 │       Agentic SQL Orchestrator      │
                 │            LangGraph                │
                 └─────────────────┬──────────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
      ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
      │ Intent      │      │ Schema       │      │ Query        │
      │ Agent       │      │ Retrieval    │      │ Planner      │
      │             │      │ Agent        │      │ Agent        │
      └─────────────┘      └──────┬───────┘      └──────┬───────┘
                                  │                     │
                                  ▼                     │
                         ┌────────────────┐             │
                         │   FalkorDB     │◄────────────┘
                         │                │
                         │ Graph Semantic │
                         │     Layer      │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │ Schema +       │
                         │ Business       │
                         │ Context       │
                         └────────────────┘

                                   │
                                   ▼
                         ┌────────────────┐
                         │ Ollama LLM     │
                         │                │
                         │ Local Models   │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │ SQL Generator  │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │ SQL Validator  │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │ SQL Database   │
                         │                │
                         │ SQLite /       │
                         │ PostgreSQL     │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │ Result Analyst │
                         │ + Explanation  │
                         └────────────────┘



Chinook database

Artist
   │
   └── Album
          │
          └── Track
                 │
                 └── InvoiceLine
                         │
                         └── Invoice
                                │
                                └── Customer


Other free databases

| Database               | Best use                    |
| ---------------------- | --------------------------- |
| **Chinook**            | ⭐ Best starting point       |
| **Northwind**          | ⭐ Excellent second database |
| AdventureWorks         | Larger SQL learning         |
| Pagila                 | PostgreSQL                  |
| Sakila                 | MySQL                       |
| NYC Taxi               | Large-scale analytics       |
| Netflix-style datasets | Analytics / aggregation     |


                    User Query
                        │
                        ▼
                ┌───────────────┐
                │ Intent Agent  │
                └───────┬───────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Planning Agent    │
              └─────────┬─────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Semantic Retrieval  │
             │ Agent               │
             └──────────┬──────────┘
                        │
                        ▼
                   FalkorDB
                        │
                        ▼
              ┌───────────────────┐
              │ SQL Generation    │
              │ Agent             │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ SQL Validation     │
              │ Agent              │
              └─────────┬─────────┘
                        │
                 ┌──────┴──────┐
                 │             │
              Valid          Invalid
                 │             │
                 │        Self Correction
                 │             │
                 └──────┬──────┘
                        ▼
                 SQL Execution
                        │
                        ▼
                 Result Analyst
                        │
                        ▼
                 Final Response


Explainability

Question
───────────────
Who are the top 5 artists by sales?

Intent
───────────────
Sales analysis

Semantic concepts
──────────────────
Artist
Track
InvoiceLine
Invoice

Join path
─────────
Artist
  ↓
Album
  ↓
Track
  ↓
InvoiceLine
  ↓
Invoice

Generated SQL
───────────────
SELECT ...

Validation
──────────
✓ Syntax valid
✓ Tables valid
✓ Columns valid
✓ Join path valid

Execution
─────────
✓ Successful

Confidence
──────────
92%

Answer
──────
The top 5 artists are...


Evaluation

Question                     Expected SQL
------------------------------------------------
Top 5 artists                SQL-001
Revenue by country           SQL-002
Best selling album           SQL-003
Customers from Brazil        SQL-004
Monthly revenue              SQL-005


SQL execution accuracy
SQL semantic accuracy
Schema selection accuracy
Join-path accuracy
Answer accuracy
Correction rate
Latency
Token usage
Confidence calibration

Production-style architecture

                         React / HTML
                              │
                              ▼
                           FastAPI
                              │
                              ▼
                         LangGraph
                              │
          ┌───────────────────┼──────────────────┐
          │                   │                  │
          ▼                   ▼                  ▼
      FalkorDB             Ollama             SQL DB
      Semantic             LLM                 Data
       Layer
          │
          ▼
       Metadata
          │
          ▼
     Observability
          │
          ▼
      Evaluation
          │
          ▼
       Feedback




