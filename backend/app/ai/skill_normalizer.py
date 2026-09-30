import re
from typing import Any, Dict, List, Optional, Set


class SkillGraph:
    """
    Canonical skill layer and ontology graph.
    Provides canonical name resolution, alias mapping, category hierarchy,
    and semantic relationship matching.
    """

    CANONICAL_SKILLS: Dict[str, Dict[str, Any]] = {
        "PostgreSQL": {
            "canonical": "PostgreSQL",
            "aliases": ["postgres", "postgresql db", "postgressql", "psql", "pgsql"],
            "category": "database",
            "parent": "SQL Databases",
            "related": ["SQL", "Relational Databases", "Database Design", "Supabase", "pgvector"],
        },
        "React": {
            "canonical": "React",
            "aliases": ["react.js", "reactjs", "react framework"],
            "category": "frontend",
            "parent": "Frontend Development",
            "related": ["JavaScript", "TypeScript", "Next.js", "Redux", "Frontend", "HTML5", "CSS3"],
        },
        "Kubernetes": {
            "canonical": "Kubernetes",
            "aliases": ["k8s", "k8", "kube", "kubernetes cluster"],
            "category": "cloud_devops",
            "parent": "Container Orchestration",
            "related": ["Docker", "DevOps", "Helm", "Cloud Native", "CI/CD", "AWS EKS", "GKE"],
        },
        "Docker": {
            "canonical": "Docker",
            "aliases": ["docker container", "dockerization", "containerization"],
            "category": "cloud_devops",
            "parent": "Containers",
            "related": ["Kubernetes", "DevOps", "CI/CD", "Linux", "Microservices"],
        },
        "PyTorch": {
            "canonical": "PyTorch",
            "aliases": ["torch", "pytorch library"],
            "category": "ai_ml",
            "parent": "Deep Learning",
            "related": ["Python", "Machine Learning", "Deep Learning", "Transformers", "CUDA", "TensorFlow"],
        },
        "TensorFlow": {
            "canonical": "TensorFlow",
            "aliases": ["tf", "tensorflow 2", "keras"],
            "category": "ai_ml",
            "parent": "Deep Learning",
            "related": ["Python", "Machine Learning", "Deep Learning", "PyTorch"],
        },
        "FastAPI": {
            "canonical": "FastAPI",
            "aliases": ["fastapi framework", "fast api"],
            "category": "backend",
            "parent": "Python Web Frameworks",
            "related": ["Python", "Pydantic", "Starlette", "REST API", "AsyncIO", "Uvicorn"],
        },
        "Python": {
            "canonical": "Python",
            "aliases": ["py", "python 3", "python3"],
            "category": "languages",
            "parent": "Programming Languages",
            "related": ["FastAPI", "Django", "Flask", "Pandas", "NumPy", "Data Science", "Backend"],
        },
        "TypeScript": {
            "canonical": "TypeScript",
            "aliases": ["ts", "typescript lang"],
            "category": "languages",
            "parent": "Programming Languages",
            "related": ["JavaScript", "React", "Node.js", "Frontend", "Fullstack"],
        },
        "JavaScript": {
            "canonical": "JavaScript",
            "aliases": ["js", "es6", "vanilla js", "ecmascript"],
            "category": "languages",
            "parent": "Programming Languages",
            "related": ["TypeScript", "React", "Node.js", "Web Development"],
        },
        "Node.js": {
            "canonical": "Node.js",
            "aliases": ["nodejs", "node", "node js"],
            "category": "backend",
            "parent": "JavaScript Runtimes",
            "related": ["Express", "JavaScript", "TypeScript", "Backend", "REST API"],
        },
        "Redis": {
            "canonical": "Redis",
            "aliases": ["redis cache", "redis key-value"],
            "category": "database",
            "parent": "NoSQL In-Memory",
            "related": ["Caching", "Message Queue", "Celery", "Backend Performance"],
        },
        "MongoDB": {
            "canonical": "MongoDB",
            "aliases": ["mongo", "mongodb atlas"],
            "category": "database",
            "parent": "NoSQL Document",
            "related": ["NoSQL", "Mongoose", "Database", "Backend"],
        },
        "GraphQL": {
            "canonical": "GraphQL",
            "aliases": ["gql", "apollo graphql"],
            "category": "api",
            "parent": "API Technologies",
            "related": ["REST API", "Apollo", "Schema Design", "Backend"],
        },
        "Amazon Web Services": {
            "canonical": "Amazon Web Services",
            "aliases": ["aws", "amazon cloud", "aws cloud"],
            "category": "cloud_devops",
            "parent": "Cloud Computing",
            "related": ["Cloud", "S3", "EC2", "Lambda", "DevOps", "Infrastructure"],
        },
        "Google Cloud Platform": {
            "canonical": "Google Cloud Platform",
            "aliases": ["gcp", "google cloud"],
            "category": "cloud_devops",
            "parent": "Cloud Computing",
            "related": ["Cloud", "BigQuery", "GKE", "DevOps"],
        },
        "LangChain": {
            "canonical": "LangChain",
            "aliases": ["langchain framework"],
            "category": "ai_ml",
            "parent": "LLM Orchestration",
            "related": ["LangGraph", "LLMs", "RAG", "Embeddings", "Prompt Engineering"],
        },
        "LangGraph": {
            "canonical": "LangGraph",
            "aliases": ["langgraph orchestrator", "lang graph"],
            "category": "ai_ml",
            "parent": "LLM Orchestration",
            "related": ["LangChain", "Multi-Agent", "StateGraph", "Workflows"],
        },
        "Vector Databases": {
            "canonical": "Vector Databases",
            "aliases": ["pgvector", "pinecone", "weaviate", "qdrant", "chromadb", "vector search"],
            "category": "database",
            "parent": "AI Data Stores",
            "related": ["RAG", "Embeddings", "ANN Search", "HNSW", "PostgreSQL"],
        },
        "Retrieval-Augmented Generation": {
            "canonical": "Retrieval-Augmented Generation",
            "aliases": ["rag", "hybrid rag", "retrieval augmented generation"],
            "category": "ai_ml",
            "parent": "AI Architectures",
            "related": ["Vector Databases", "Embeddings", "Reranking", "LLMs", "Hybrid Search"],
        },
    }

    def __init__(self):
        # Build quick alias lookup map
        self.alias_to_canonical: Dict[str, str] = {}
        for canonical, data in self.CANONICAL_SKILLS.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in data.get("aliases", []):
                self.alias_to_canonical[alias.lower()] = canonical

    def normalize(self, skill_name: str) -> Dict[str, Any]:
        """
        Normalizes a raw skill string to canonical entity.
        Returns a dict with canonical name, original input, category, and aliases.
        """
        cleaned = skill_name.strip()
        cleaned_lower = cleaned.lower()

        # Direct canonical or alias match
        if cleaned_lower in self.alias_to_canonical:
            canonical_name = self.alias_to_canonical[cleaned_lower]
            info = self.CANONICAL_SKILLS[canonical_name]
            return {
                "raw": skill_name,
                "canonical": canonical_name,
                "category": info.get("category", "general"),
                "parent": info.get("parent"),
                "aliases": info.get("aliases", []),
                "related": info.get("related", []),
                "is_normalized": True,
            }

        # Token-based match (e.g. "expert in postgresql" -> "PostgreSQL")
        words = re.findall(r"\b[a-zA-Z0-9+#\.]+\b", cleaned_lower)
        for w in words:
            if w in self.alias_to_canonical:
                canonical_name = self.alias_to_canonical[w]
                info = self.CANONICAL_SKILLS[canonical_name]
                return {
                    "raw": skill_name,
                    "canonical": canonical_name,
                    "category": info.get("category", "general"),
                    "parent": info.get("parent"),
                    "aliases": info.get("aliases", []),
                    "related": info.get("related", []),
                    "is_normalized": True,
                }

        # Title-cased fallback if not in dictionary
        formatted = " ".join(word.capitalize() for word in cleaned.split())
        return {
            "raw": skill_name,
            "canonical": formatted,
            "category": "general",
            "parent": None,
            "aliases": [],
            "related": [],
            "is_normalized": False,
        }

    def match_skills(self, skill_a: str, skill_b: str) -> bool:
        """
        Evaluates whether two skill names represent the same competence,
        checking canonical representations, aliases, and substring bounds.
        """
        if not skill_a or not skill_b:
            return False

        norm_a = self.normalize(skill_a)
        norm_b = self.normalize(skill_b)

        # Same canonical name
        if norm_a["canonical"].lower() == norm_b["canonical"].lower():
            return True

        # Check aliases mutual inclusion
        aliases_a = {a.lower() for a in norm_a.get("aliases", [])}
        aliases_b = {b.lower() for b in norm_b.get("aliases", [])}
        if aliases_a.intersection(aliases_b):
            return True

        # Exact normalized match
        clean_a = re.sub(r"[^a-zA-Z0-9]", "", skill_a).lower()
        clean_b = re.sub(r"[^a-zA-Z0-9]", "", skill_b).lower()
        return clean_a == clean_b


skill_normalizer = SkillGraph()
