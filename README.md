# Medical Education Oral Presentation Grading System

A modular, microservices-based **Rubric-Driven Grading System** for medical education oral presentations. This system provides citation-gated, deterministic feedback where every piece of feedback references specific rubric anchors and student transcript timestamps.

## 🎯 Core Features

- **Citation-Gated Feedback**: Every feedback item cites rubric anchors and student transcript spans
- **Deterministic Scoring**: Mathematical formulas ensure reproducible results
- **Self-Contained Rubrics**: All grading logic lives in JSON rubric files
- **Microservices Architecture**: Independent, containerized services
- **Zero Hallucination**: No feedback without explicit rubric backing

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Services](#services)
- [Rubric Structure](#rubric-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## 🏗️ System Architecture

The system consists of independent microservices that communicate via RESTful APIs:

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│ Rubric Mgmt    │   │ Structure       │   │ Scoring        │
│ Service        │   │ Evaluator       │   │ Service        │
│ Port: 8001     │   │ Port: 8004      │   │ Port: 8007     │
└────────────────┘   └─────────────────┘   └────────────────┘
                              │
                     ┌────────▼────────┐
                     │ Feedback        │
                     │ Composer        │
                     │ Port: 8008      │
                     └─────────────────┘
```

### All Services (Complete System)

1. **Grading Orchestrator Service** (Port 8000) ⭐ **Main Entry Point**
   - Coordinates complete grading workflow
   - Calls all services in proper sequence
   - Parallel evaluation where possible
   - Returns complete grading results

2. **Rubric Management Service** (Port 8001)
   - CRUD operations for rubrics
   - Versioning and approval workflow
   - JSON file storage

3. **Transcript Processing Service** (Port 8002)
   - Parses raw transcript text
   - Segments into clinical sections
   - Detects section boundaries

4. **Question Matching Service** (Port 8003)
   - BM25 lexical matching
   - Sentence embedding semantic matching
   - Hybrid scoring for robust detection

5. **Structure Evaluator Service** (Port 8004)
   - Validates section order using LCS algorithm
   - Detects missing and out-of-order sections
   - Applies penalties

6. **Reasoning Evaluator Service** (Port 8005)
   - Pattern-based reasoning link detection
   - Dual citation requirement
   - Context extraction

7. **Summary Evaluator Service** (Port 8006)
   - Token counting for succinctness
   - Required element detection
   - Combined scoring (50/50)

8. **Scoring Service** (Port 8007)
   - Applies weighted scoring formulas
   - Computes overall score from components
   - Provides detailed breakdown

9. **Feedback Composer Service** (Port 8008)
   - Generates natural language feedback
   - Ensures all feedback has citations
   - Supports multiple feedback styles

10. **QA Validation Service** (Port 8010)
    - Validates rubrics before approval
    - Checks weights, anchors, questions
    - Returns detailed validation report

### Future Services (Phase 3)

- Teacher Edit Service (Port 8009) - NLP-based rubric editing

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd med-ed-op-grader
```

2. Start all services using Docker Compose:
```bash
docker-compose up --build
```

3. Verify services are running:
```bash
# Check Orchestrator (main service)
curl http://localhost:8000/health

# Check all services status
curl http://localhost:8000/services/status
```

### Example Usage

#### Complete Grading Workflow (Recommended)

Use the Grading Orchestrator for end-to-end grading:

```bash
# 1. First, create a rubric
curl -X POST http://localhost:8001/rubrics \
  -H "Content-Type: application/json" \
  -d @data/rubrics/examples/stroke_v1.json

# 2. Grade a presentation (one API call does everything!)
curl -X POST http://localhost:8000/grade \
  -H "Content-Type: application/json" \
  -d '{
    "rubric_id": "stroke_v1",
    "transcript_id": "stroke_001",
    "raw_text": "[00:05] Student: Tell me what brings you in today?\n[00:08] Patient: I have sudden weakness on my left side.\n[00:15] Student: When did you first notice the weakness?\n[00:18] Patient: About 2 hours ago.\n[01:35] Student: So to summarize, this is a 65-year-old male with sudden onset left-sided weakness concerning for stroke."
  }'
```

This single API call will:
- Parse and segment the transcript
- Evaluate structure, questions, reasoning, and summary
- Compute weighted scores
- Generate cited feedback
- Return complete grading results

#### Individual Service Usage

You can also call services individually:

```bash
# Parse transcript
curl -X POST http://localhost:8002/transcripts/process \
  -H "Content-Type: application/json" \
  -d @data/examples/stroke_transcript_001.txt

# Match questions
curl -X POST http://localhost:8003/match/questions \
  -H "Content-Type: application/json" \
  -d '{...}'

# Evaluate structure
curl -X POST http://localhost:8004/evaluate/structure \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 📦 Services

### Rubric Management Service

**Endpoints:**
- `POST /rubrics` - Create new rubric
- `GET /rubrics/{id}` - Retrieve rubric
- `GET /rubrics/{id}/versions` - List versions
- `PUT /rubrics/{id}` - Update rubric (creates new version)
- `PATCH /rubrics/{id}` - Apply JSON Patch operations
- `POST /rubrics/{id}/approve` - Approve rubric
- `DELETE /rubrics/{id}` - Delete rubric version

**Features:**
- JSON file storage with versioning
- Semantic versioning (X.Y.Z)
- Draft/Approved/Archived status
- Unique anchor validation

### Structure Evaluator Service

**Endpoints:**
- `POST /evaluate/structure` - Evaluate presentation structure

**Algorithm:**
- Uses Longest Common Subsequence (LCS) for base score
- Applies penalties for violations
- Detects missing and out-of-order sections

**Formula:**
```
structure_score = clamp(LCS(detected, expected) / len(expected) + Σ penalties, 0, 1)
```

### Scoring Service

**Endpoints:**
- `POST /score/compute` - Compute weighted final score

**Formula:**
```
overall = w_struct*structure + w_keys*keys + w_reason*reason + w_summary*summary
```

Where weights must sum to 1.0.

### Feedback Composer Service

**Endpoints:**
- `POST /feedback/compose` - Generate cited feedback

**Features:**
- Template-based feedback generation
- Citation validation (all feedback must cite rubric)
- Multiple styles: constructive, detailed, concise

## 📝 Rubric Structure

Rubrics are JSON files with the following structure:

```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "approved",
  "weights": {
    "structure": 0.2,
    "key_questions": 0.4,
    "reasoning": 0.25,
    "summary": 0.15
  },
  "structure": {
    "anchor": "#R.structure",
    "expected_order": ["CC", "HPI", "ROS", "PMH", "SH", "FH", "Summary"],
    "penalties": [...]
  },
  "key_questions": [...],
  "reasoning": {...},
  "summary": {...}
}
```

### Example Rubrics

- `data/rubrics/examples/stroke_v1.json` - Stroke presentation rubric
- `data/rubrics/examples/chest_pain_v1.json` - Chest pain presentation rubric

## 📚 API Documentation

Each service provides auto-generated OpenAPI documentation:

- Rubric Management: http://localhost:8001/docs
- Structure Evaluator: http://localhost:8004/docs
- Scoring: http://localhost:8007/docs
- Feedback Composer: http://localhost:8008/docs

## 🛠️ Development

### Local Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies for a service:
```bash
cd services/rubric_management
pip install -r requirements.txt
```

3. Run a service locally:
```bash
python -m uvicorn services.rubric_management.app.main:app --reload --port 8001
```

### Project Structure

```
med-ed-op-grader/
├── services/
│   ├── rubric_management/
│   ├── structure_evaluator/
│   ├── scoring/
│   └── feedback_composer/
├── shared/
│   ├── models/          # Shared Pydantic models
│   └── utils/           # Shared utilities
├── data/
│   ├── rubrics/         # Rubric JSON files
│   └── examples/        # Example data
├── docker-compose.yml
├── SYSTEM_GUIDE.md      # Comprehensive system documentation
└── README.md
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run tests for a specific service
pytest services/rubric_management/tests/

# Run with coverage
pytest --cov=services --cov-report=html
```

### Integration Tests

```bash
pytest tests/integration/
```

## 🚢 Deployment

### Docker Deployment

Build and run all services:
```bash
docker-compose up --build -d
```

Stop all services:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

### AWS Deployment (Planned)

Deployment to AWS will use:
- ECS/Fargate for container orchestration
- Application Load Balancer for routing
- RDS or DocumentDB for production storage
- CloudWatch for monitoring

## 🧪 Testing

### Integration Tests

Run comprehensive end-to-end tests:

```bash
# Run all integration tests
./run_integration_tests.sh

# Or use pytest directly
pytest tests/integration/test_complete_workflow.py -v
```

**Test Coverage**:
- Service health checks
- Complete grading workflow (stroke & chest pain)
- Citation validation (100% coverage)
- Deterministic scoring verification
- Error handling

### Performance Testing

Run load tests to benchmark performance:

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/load_test.py --host=http://localhost:8000

# Open web UI at http://localhost:8089
```

**Performance Targets**:
- Throughput: 10+ requests/second
- Latency: p95 < 5 seconds
- Error Rate: < 1%
- Concurrent Users: 50+

### Manual Testing

Test the complete system manually:

```bash
# Run complete system test
./test_complete_system.sh
```

This script will:
- Check service health
- Create rubrics
- Grade presentations
- Validate citations
- Display detailed results

---

## 📖 Documentation

- **SYSTEM_GUIDE.md** - Comprehensive system architecture and design documentation
- **DEPLOYMENT.md** - Production deployment guide (Docker, AWS, monitoring)
- **PHASE_2_COMPLETE.md** - Phase 2 implementation summary
- **PHASE_3_COMPLETE.md** - Phase 3 testing and production readiness
- **API Documentation** - Auto-generated OpenAPI docs at `/docs` endpoint for each service

## 🎯 Roadmap

### Phase 1: MVP Core ✅ COMPLETE
- [x] System architecture and documentation
- [x] Rubric Management Service
- [x] Structure Evaluator Service
- [x] Scoring Service
- [x] Feedback Composer Service
- [x] Docker containerization
- [x] Basic CI/CD pipeline

### Phase 2: Enhancement Services ✅ COMPLETE
- [x] Transcript Processing Service
- [x] Question Matching Service (BM25 + embeddings)
- [x] Reasoning Evaluator Service
- [x] Summary Evaluator Service
- [x] QA Validation Service
- [x] Grading Orchestrator Service

### Phase 3: Integration Testing & Production Readiness ✅ COMPLETE
- [x] Integration testing suite (9 comprehensive tests)
- [x] Example transcripts (stroke, chest pain)
- [x] Prometheus metrics integration
- [x] Complete deployment documentation
- [x] Performance testing framework (Locust)
- [x] Production readiness validation

### Phase 4: Optional Enhancements (Future)
- [ ] Teacher Edit Service (NLP-based rubric editing)
- [ ] API authentication and rate limiting
- [ ] Database migration (PostgreSQL/MongoDB)
- [ ] Advanced analytics dashboard
- [ ] Multi-tenancy support
- [ ] Real-time grading with WebSockets

## 🤝 Contributing

1. Follow the microservices architecture
2. Ensure all feedback has proper citations
3. Write tests for new features
4. Update SYSTEM_GUIDE.md for architectural changes

## 📄 License

[License information to be added]

## 📧 Contact

[Contact information to be added]

