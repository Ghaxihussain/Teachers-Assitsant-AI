#  Teacher TA AI — Intelligent Teaching Assistant Backend

A backend system that acts as an AI-powered teaching assistant. Teachers can upload course material and give behavioral instructions to the AI, and students can query it in natural language to get answers grounded in the actual course content.

---

##  What It Does

**For Teachers:**
- Upload PDF or text course materials — the system automatically processes, chunks, and stores them as searchable vector embeddings
- Add behavioral instructions to guide how the AI responds to students (e.g. *"always respond formally"* or *"don't give direct answers, guide the student instead"*)
- Delete uploaded files or instructions anytime
- View all uploaded files and active instructions

**For Students:**
- Ask any question in natural language
- The AI searches through the uploaded course material, finds the most relevant content, and generates a proper answer — grounded only in what the teacher has actually uploaded, nothing made up

---

##  API Overview

| Method | Endpoint | Who | What it does |
|--------|----------|-----|--------------|
| `POST` | `/teacher/upload` | Teacher | Upload a PDF/text file and optionally add an instruction |
| `DELETE` | `/teacher/delete/file/{filename}` | Teacher | Remove an uploaded file |
| `DELETE` | `/teacher/delete/instruction/{id}` | Teacher | Remove a specific instruction |
| `GET` | `/teacher/instructions` | Teacher | View all active instructions |
| `GET` | `/teacher/files` | Teacher | View all uploaded files |
| `GET` | `/student/invoke/{query}` | Student | Ask the AI a question |

---

##  Tech Stack

| Tool | Purpose |
|------|---------|
| **FastAPI** | REST API backend |
| **PostgreSQL + pgvector** | Stores vector embeddings, enables semantic similarity search |
| **OpenAI GPT-4o** | Generates answers and summarizes visual content |
| **OpenAI text-embedding-3-small** | Converts text into vector embeddings |
| **Unstructured** | Parses PDFs — text, tables, and images |
| **AWS S3** | Stores the actual uploaded files |
| **SQLAlchemy (async)** | Async database ORM |
| **Docker** | Runs PostgreSQL locally |

---

## ⚙️ How the RAG Pipeline Works

```
Teacher uploads PDF
       ↓
File stored in AWS S3
       ↓
PDF parsed by Unstructured (text + tables + images)
       ↓
Content split into chunks (title-based chunking)
       ↓
Each chunk embedded via OpenAI text-embedding-3-small
       ↓
Embeddings stored in PostgreSQL via pgvector
       ↓
Student asks a question
       ↓
Query embedded → 3 most similar chunks retrieved
       ↓
2 most relevant teacher instructions retrieved
       ↓
GPT-4o generates final answer using context + instructions
```

---

##  Challenges & How I Solved Them

**File Storage**
Had no strategy for storing actual uploaded files initially. Integrated AWS S3 with boto3 so files are stored in the cloud and fetched by URL when processing begins.

**Unstructured URL Parsing**
`unstructured`'s `partition_pdf` doesn't accept a URL directly. Fixed by downloading the file from S3 first using `requests` and passing it as a `BytesIO` object.

**Instructions as a Separate Vector Table**
Needed teacher instructions to influence AI behavior dynamically, not just be hardcoded in a system prompt. Built a separate `instructions` table with its own embeddings so the most contextually relevant instructions are retrieved per query.

**PostgreSQL Auth in Docker**
Resolved persistent connection issues by setting `POSTGRES_HOST_AUTH_METHOD: trust` in Docker Compose during development.

---

##  Planned Improvements

- [ ] Add chat history for multi-turn student conversations
- [ ] Store file metadata (upload date, file size, page count) in a dedicated table
- [ ] Email agent — teacher types a casual message, AI drafts a formal email and sends it to all students automatically
- [ ] Teacher dashboard frontend
- [ ] Separate metadata DB from vector DB

---

##  What I Learned

- Building a full RAG pipeline from scratch without LangChain or any framework
- Chunking strategies and why title-based chunking works well for structured documents
- How pgvector enables semantic search natively inside PostgreSQL
- Async database operations with SQLAlchemy
- Multimodal document processing — handling text, tables, and images from the same PDF
- AWS S3 integration for cloud file storage in a production-style backend

---

