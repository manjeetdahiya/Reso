export PYTHONPATH=.:$PYTHONPATH
uvicorn src.orchestrator.server:app --reload --port 8008