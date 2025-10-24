# Quick Start Guide

This guide will help you get the Medical Education Oral Presentation Grading System up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (optional, for local testing)
- Git

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd med-ed-op-grader

# Verify directory structure
ls -la
```

You should see:
- `services/` - Microservices
- `shared/` - Shared models and utilities
- `data/` - Rubrics and examples
- `docker-compose.yml` - Service orchestration
- `SYSTEM_GUIDE.md` - Complete documentation

## Step 2: Run the Test Demo (Optional)

Before starting the services, you can run a local test to see how the system works:

```bash
# Install Python dependencies
pip install pydantic fastapi

# Run the test demo
python test_system.py
```

This will:
1. Load the stroke_v1 rubric
2. Create a sample transcript
3. Evaluate the structure
4. Compute scores
5. Generate cited feedback

## Step 3: Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

This will start:
- **Rubric Management Service** on port 8001
- **Structure Evaluator Service** on port 8004
- **Scoring Service** on port 8007
- **Feedback Composer Service** on port 8008

## Step 4: Verify Services

Check that all services are healthy:

```bash
# Check Rubric Management
curl http://localhost:8001/health

# Check Structure Evaluator
curl http://localhost:8004/health

# Check Scoring
curl http://localhost:8007/health

# Check Feedback Composer
curl http://localhost:8008/health
```

Each should return: `{"status": "healthy", "service": "<service_name>"}`

## Step 5: Explore API Documentation

Open your browser and visit the auto-generated API documentation:

- Rubric Management: http://localhost:8001/docs
- Structure Evaluator: http://localhost:8004/docs
- Scoring: http://localhost:8007/docs
- Feedback Composer: http://localhost:8008/docs

## Step 6: Try the APIs

### Create a Rubric

```bash
curl -X POST http://localhost:8001/rubrics \
  -H "Content-Type: application/json" \
  -d @data/rubrics/examples/stroke_v1.json
```

### Retrieve a Rubric

```bash
curl http://localhost:8001/rubrics/stroke_v1 | jq
```

### List Rubric Versions

```bash
curl http://localhost:8001/rubrics/stroke_v1/versions | jq
```

### Evaluate Structure

Create a file `structure_request.json`:

```json
{
  "rubric_id": "stroke_v1",
  "structure_config": {
    "anchor": "#R.structure",
    "expected_order": ["CC", "HPI", "ROS", "PMH", "SH", "FH", "Summary"],
    "penalties": [
      {
        "id": "missing_summary",
        "anchor": "#R.structure.penalty.missing_summary",
        "description": "Missing summary section",
        "value": -0.3
      }
    ]
  },
  "segmented_transcript": {
    "transcript_id": "test_001",
    "sections": [
      {
        "label": "CC",
        "utterances": [],
        "timestamp_start": "00:00",
        "timestamp_end": "00:10"
      },
      {
        "label": "HPI",
        "utterances": [],
        "timestamp_start": "00:10",
        "timestamp_end": "01:00"
      }
    ],
    "detected_order": ["CC", "HPI"]
  }
}
```

Then evaluate:

```bash
curl -X POST http://localhost:8004/evaluate/structure \
  -H "Content-Type: application/json" \
  -d @structure_request.json | jq
```

### Compute Score

Create a file `score_request.json`:

```json
{
  "rubric_weights": {
    "structure": 0.2,
    "key_questions": 0.4,
    "reasoning": 0.25,
    "summary": 0.15,
    "communication": 0.0
  },
  "component_scores": {
    "structure": 0.65,
    "key_questions": 0.80,
    "reasoning": 0.50,
    "summary": 0.75,
    "communication": 0.0
  }
}
```

Then compute:

```bash
curl -X POST http://localhost:8007/score/compute \
  -H "Content-Type: application/json" \
  -d @score_request.json | jq
```

## Step 7: View Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs rubric-management
```

## Step 8: Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Next Steps

1. **Read the Documentation**
   - `SYSTEM_GUIDE.md` - Complete system architecture and design
   - `README.md` - Project overview and features

2. **Implement Remaining Services**
   - Transcript Processing Service
   - Question Matching Service
   - Reasoning Evaluator Service
   - Summary Evaluator Service
   - Grading Orchestrator Service

3. **Add Tests**
   - Unit tests for each service
   - Integration tests for service interactions
   - End-to-end grading workflow tests

4. **Customize Rubrics**
   - Create new rubrics for different presentations
   - Modify existing rubrics using the API
   - Use JSON Patch for fine-grained updates

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker --version
docker-compose --version

# Check for port conflicts
lsof -i :8001
lsof -i :8004
lsof -i :8007
lsof -i :8008
```

### Import errors in test_system.py

```bash
# Make sure you're in the project root
pwd

# Install required packages
pip install pydantic fastapi
```

### Docker build fails

```bash
# Clean up Docker
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

## Getting Help

- Check `SYSTEM_GUIDE.md` for detailed documentation
- Review API docs at `/docs` endpoints
- Examine example rubrics in `data/rubrics/examples/`
- Run `python test_system.py` to see a working example

## Key Concepts

### Citations
Every feedback item must include:
- **Rubric citation**: `rubric://<rubric_id>#<anchor>`
- **Student citation**: `student://oral#<timestamp_start>–<timestamp_end>`

### Rubric Structure
Rubrics are JSON files with:
- Weights (must sum to 1.0)
- Structure configuration (expected order, penalties)
- Key questions (with critical flag)
- Reasoning links (required clinical connections)
- Summary requirements (token limits, required elements)

### Scoring Formulas
- **Structure**: LCS-based with penalties
- **Questions**: Weighted coverage (critical=2.0, non-critical=1.0)
- **Reasoning**: Ratio of detected to required links
- **Summary**: 50% succinctness + 50% completeness
- **Overall**: Weighted sum of components

## Example Workflow

1. **Create/Load Rubric** → Rubric Management Service
2. **Parse Transcript** → Transcript Processing Service (Phase 2)
3. **Evaluate Components** → Structure, Questions, Reasoning, Summary Evaluators
4. **Compute Score** → Scoring Service
5. **Generate Feedback** → Feedback Composer Service
6. **Return Results** → Grading Orchestrator (Phase 2)

Happy grading! 🎓

