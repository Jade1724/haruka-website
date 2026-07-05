"""mecha-haruka offline RAG pipeline and evaluation harness.

This package holds *only* the asynchronous, offline setup logic for the
mecha-haruka chatbot: pulling content sources, chunking, embedding, and building
the Azure AI Search index, plus the evaluation harness. Real-time chat lives in
the backend (`backend/app`) and frontend (`frontend/components/chat`).
"""
