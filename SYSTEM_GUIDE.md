# Medical Education Oral Presentation Grading System - System Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Design Principles](#design-principles)
4. [Rubric Schema Specification](#rubric-schema-specification)
5. [Scoring Formulas](#scoring-formulas)
6. [Service APIs](#service-apis)
7. [Data Contracts](#data-contracts)
8. [Citation System](#citation-system)
9. [Implementation Notes](#implementation-notes)
10. [Decision Log](#decision-log)

---

## System Overview

### Purpose
A deterministic, citation-gated grading system for medical education oral presentations that provides feedback anchored to explicit rubric criteria and student transcript evidence.

### Core Principles
- **Zero Hallucination**: No feedback without explicit rubric backing
- **Deterministic Scoring**: Mathematical formulas over pattern matching
- **Citation-Gated**: Every feedback item cites rubric anchors and student spans
- **Self-Contained Rubrics**: All grading logic lives in rubric JSON
- **Microservices Architecture**: Independent, containerized services

---

## Architecture

### System Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│ Rubric Mgmt    │   │ Grading         │   │ Teacher Edit   │
│ Service        │   │ Orchestrator    │   │ Service        │
└───────┬────────┘   └────────┬────────┘   └───────┬────────┘
        │                     │                     │
        │            ┌────────┴────────┐           │
        │            │                 │           │
        │    ┌───────▼────────┐ ┌─────▼──────┐   │
        │    │ Transcript     │ │ QA         │   │
        │    │ Processing     │ │ Validation │   │
        │    └───────┬────────┘ └────────────┘   │
        │            │                             │
        │    ┌───────┴────────┐                   │
        │    │                │                   │
        │ ┌──▼──────────┐ ┌──▼──────────┐       │
        │ │ Structure   │ │ Question    │       │
        │ │ Evaluator   │ │ Matching    │       │
        │ └──┬──────────┘ └──┬──────────┘       │
        │    │               │                   │
        │ ┌──▼──────────┐ ┌──▼──────────┐       │
        │ │ Reasoning   │ │ Summary     │       │
        │ │ Evaluator   │ │ Evaluator   │       │
        │ └──┬──────────┘ └──┬──────────┘       │
        │    │               │                   │
        │    └───────┬───────┘                   │
        │            │                           │
        │    ┌───────▼────────┐                 │
        │    │ Scoring        │                 │
        │    │ Service        │                 │
        │    └───────┬────────┘                 │
        │            │                           │
        │    ┌───────▼────────┐                 │
        │    │ Feedback       │                 │
        │    │ Composer       │                 │
        │    └────────────────┘                 │
        │                                        │
        └────────────────────────────────────────┘
```

### Microservices

#### 1. Rubric Management Service
**Responsibility**: CRUD operations, versioning, storage
- **Port**: 8001
- **Endpoints**:
  - `POST /rubrics` - Create new rubric
  - `GET /rubrics/{id}` - Retrieve rubric
  - `GET /rubrics/{id}/versions` - List versions
  - `PUT /rubrics/{id}` - Update rubric (creates new version)
  - `PATCH /rubrics/{id}` - Apply JSON Patch
  - `POST /rubrics/{id}/approve` - Approve rubric version
- **Storage**: JSON files or document database

#### 2. Transcript Processing Service
**Responsibility**: Parse and segment student transcripts
- **Port**: 8002
- **Endpoints**:
  - `POST /transcripts/parse` - Parse raw transcript
  - `POST /transcripts/segment` - Segment into sections
- **Input**: Raw transcript with timestamps
- **Output**: Structured sections with metadata

#### 3. Question Matching Service
**Responsibility**: Match student questions against rubric phrases
- **Port**: 8003
- **Endpoints**:
  - `POST /match/questions` - Match questions using BM25 + embeddings
- **Algorithms**: BM25 for phrase matching, sentence embeddings for semantic similarity
- **Output**: Matched questions with confidence scores and citations

#### 4. Structure Evaluator Service
**Responsibility**: Validate section order and completeness
- **Port**: 8004
- **Endpoints**:
  - `POST /evaluate/structure` - Evaluate structure
- **Algorithm**: Longest Common Subsequence (LCS) + penalty application
- **Output**: Structure score + violations with citations

#### 5. Reasoning Evaluator Service
**Responsibility**: Detect clinical reasoning patterns
- **Port**: 8005
- **Endpoints**:
  - `POST /evaluate/reasoning` - Evaluate reasoning links
- **Algorithm**: Pattern matching with dual citation requirement
- **Output**: Reasoning score + detected/missing links with citations

#### 6. Summary Evaluator Service
**Responsibility**: Validate summary constraints
- **Port**: 8006
- **Endpoints**:
  - `POST /evaluate/summary` - Evaluate summary
- **Algorithm**: Token counting + required element detection
- **Output**: Summary score + violations with citations

#### 7. Scoring Service
**Responsibility**: Apply formulas and compute final scores
- **Port**: 8007
- **Endpoints**:
  - `POST /score/compute` - Compute weighted final score
- **Input**: Individual component scores + rubric weights
- **Output**: Final score breakdown

#### 8. Feedback Composer Service
**Responsibility**: Generate natural language feedback from structured results
- **Port**: 8008
- **Endpoints**:
  - `POST /feedback/compose` - Generate cited feedback
- **Algorithm**: Template-based generation with LLM rephrasing (optional)
- **Output**: Natural language feedback with citations

#### 9. Teacher Edit Service
**Responsibility**: Convert natural language edits to JSON Patch
- **Port**: 8009
- **Endpoints**:
  - `POST /edit/parse` - Parse natural language edit request
  - `POST /edit/preview` - Preview JSON Patch operations
- **Algorithm**: NLP parsing + JSON Patch generation
- **Output**: RFC 6902 JSON Patch operations

#### 10. QA Validation Service
**Responsibility**: Auto-check rubrics before approval
- **Port**: 8010
- **Endpoints**:
  - `POST /qa/validate` - Run validation checks
- **Checks**:
  - Weights sum to 1.0
  - At least one critical question for time-sensitive diagnoses
  - All required_links have unique IDs and anchors
  - summary.max_tokens within bounds (40–120)
  - No duplicate phrases across questions
- **Output**: Validation report with pass/fail + issues

#### 11. Grading Orchestrator Service
**Responsibility**: Coordinate grading workflow across services
- **Port**: 8000
- **Endpoints**:
  - `POST /grade` - Grade a student submission
- **Workflow**:
  1. Fetch rubric from Rubric Management
  2. Parse transcript via Transcript Processing
  3. Parallel evaluation: Structure, Questions, Reasoning, Summary
  4. Aggregate scores via Scoring Service
  5. Generate feedback via Feedback Composer
  6. Return complete grading report

---

## Design Principles

### 1. Self-Contained Rubrics
All grading expectations, weights, penalties, and thresholds live inside the rubric JSON. No hardcoded logic in services.

### 2. Deterministic Scoring
Use mathematical formulas (LCS, weighted sums, ratios) over heuristics. Same input always produces same output.

### 3. Citation-Gated Feedback
Every feedback item MUST include:
- **Rubric citation**: `rubric://<rubric_id>#<anchor>`
- **Student citation** (when applicable): `student://oral#<timestamp_start>–<timestamp_end>` or `student://summary#tokens=<count>`

### 4. Zero Hallucination
LLMs only rephrase structured results into natural language. No LLM-generated feedback without explicit rubric backing.

### 5. Dual Citation Rule (Reasoning)
Clinical reasoning feedback requires BOTH rubric anchor AND student transcript span.

---

## Rubric Schema Specification

### Top-Level Structure
```json
{
  "rubric_id": "string (unique identifier)",
  "version": "string (semver: 1.0.0)",
  "status": "draft | approved | archived",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",
  "weights": {
    "structure": "float (0-1)",
    "key_questions": "float (0-1)",
    "reasoning": "float (0-1)",
    "summary": "float (0-1)",
    "communication": "float (0-1, typically 0 for MVP)"
  },
  "structure": { ... },
  "key_questions": [ ... ],
  "key_questions_policy": { ... },
  "reasoning": { ... },
  "summary": { ... },
  "communication": { ... }
}
```

### Structure Object
```json
"structure": {
  "anchor": "#R.structure",
  "expected_order": ["CC", "HPI", "ROS", "PMH", "SH", "FH", "Summary"],
  "penalties": [
    {
      "id": "swap_ros_before_hpi",
      "anchor": "#R.structure.penalty.swap_ros_before_hpi",
      "description": "ROS before HPI",
      "value": -0.2
    },
    {
      "id": "missing_summary",
      "anchor": "#R.structure.penalty.missing_summary",
      "description": "Missing summary section",
      "value": -0.3
    }
  ]
}
```

### Key Questions Array
```json
"key_questions": [
  {
    "id": "onset_time",
    "anchor": "#Q.onset_time",
    "label": "When did symptoms start?",
    "critical": true,
    "phrases": [
      "when did this start",
      "what time did you notice",
      "when were you last normal"
    ]
  }
]
```

### Key Questions Policy
```json
"key_questions_policy": {
  "anchor": "#R.key_questions",
  "critical_weight": 2.0,
  "noncritical_weight": 1.0,
  "coverage_threshold": 0.7
}
```

### Reasoning Object
```json
"reasoning": {
  "anchor": "#R.reasoning",
  "required_links": [
    {
      "id": "acute_to_stroke",
      "anchor": "#R.reason.acute_to_stroke",
      "description": "Acute focal deficit → consider stroke",
      "pattern": "acute.*focal.*stroke|stroke.*acute.*deficit"
    }
  ],
  "major_gap_penalty": -0.5
}
```

### Summary Object
```json
"summary": {
  "anchor": "#R.summary",
  "max_tokens": 80,
  "overflow_divisor": 20,
  "required_elements": [
    {
      "id": "problem",
      "anchor": "#R.summary.req.problem",
      "description": "Chief complaint or problem statement"
    },
    {
      "id": "pos2",
      "anchor": "#R.summary.req.pos2",
      "description": "At least 2 positive findings"
    }
  ]
}
```

---

## Scoring Formulas

### Structure Score
```python
def compute_structure_score(detected_order, expected_order, penalties_applied):
    """
    LCS-based structure score with penalties.
    
    Args:
        detected_order: List of detected section labels
        expected_order: List of expected section labels from rubric
        penalties_applied: List of penalty values (negative floats)
    
    Returns:
        float: Score in range [0, 1]
    """
    lcs_length = longest_common_subsequence(detected_order, expected_order)
    base_score = lcs_length / len(expected_order)
    penalty_sum = sum(penalties_applied)
    return max(0, min(1, base_score + penalty_sum))
```

### Key Questions Score
```python
def compute_key_questions_score(matched_questions, all_questions, policy):
    """
    Weighted coverage score for key questions.
    
    Args:
        matched_questions: List of matched question IDs
        all_questions: List of all question objects from rubric
        policy: key_questions_policy object
    
    Returns:
        float: Score in range [0, 1]
    """
    total_weight = sum(
        policy['critical_weight'] if q['critical'] else policy['noncritical_weight']
        for q in all_questions
    )
    matched_weight = sum(
        policy['critical_weight'] if q['critical'] else policy['noncritical_weight']
        for q in all_questions if q['id'] in matched_questions
    )
    return matched_weight / total_weight if total_weight > 0 else 0
```

### Reasoning Score
```python
def compute_reasoning_score(detected_links, required_links):
    """
    Simple ratio of detected to required reasoning links.
    
    Args:
        detected_links: List of detected link IDs (with dual citations)
        required_links: List of required link objects from rubric
    
    Returns:
        float: Score in range [0, 1]
    """
    L = len(required_links)
    H = len(detected_links)
    return H / L if L > 0 else 1.0
```

### Summary Score
```python
def compute_summary_score(token_count, max_tokens, overflow_divisor, 
                          matched_elements, required_elements):
    """
    Combined score for summary succinctness and completeness.
    
    Args:
        token_count: Actual token count in summary
        max_tokens: Maximum allowed tokens from rubric
        overflow_divisor: Penalty divisor for overflow
        matched_elements: List of matched element IDs
        required_elements: List of required element objects
    
    Returns:
        float: Score in range [0, 1]
    """
    overflow = max(0, token_count - max_tokens)
    succinct = max(0, 1 - overflow / overflow_divisor)
    
    elements = len(matched_elements) / len(required_elements) if required_elements else 1.0
    
    return 0.5 * succinct + 0.5 * elements
```

### Overall Score
```python
def compute_overall_score(component_scores, weights):
    """
    Weighted sum of component scores.
    
    Args:
        component_scores: Dict with keys: structure, key_questions, reasoning, summary
        weights: Dict with same keys, values sum to 1.0
    
    Returns:
        float: Overall score in range [0, 1]
    """
    return (
        weights['structure'] * component_scores['structure'] +
        weights['key_questions'] * component_scores['key_questions'] +
        weights['reasoning'] * component_scores['reasoning'] +
        weights['summary'] * component_scores['summary'] +
        weights.get('communication', 0) * component_scores.get('communication', 0)
    )
```

---

## Service APIs

### Data Contracts

#### Common Types
```typescript
// Citation types
type RubricCitation = `rubric://${string}#${string}`;
type StudentCitation = `student://oral#${string}–${string}` | `student://summary#tokens=${number}`;

// Timestamp format: MM:SS or HH:MM:SS
type Timestamp = string;

// Evaluation result structure
interface EvaluationResult {
  score: number;  // 0-1
  violations: Violation[];
  successes: Success[];
}

interface Violation {
  description: string;
  rubric_citations: RubricCitation[];
  student_citations?: StudentCitation[];
  severity: 'critical' | 'major' | 'minor';
}

interface Success {
  description: string;
  rubric_citations: RubricCitation[];
  student_citations?: StudentCitation[];
}
```

### 1. Rubric Management Service API

#### POST /rubrics
Create a new rubric.

**Request:**
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "draft",
  "weights": { ... },
  "structure": { ... },
  "key_questions": [ ... ],
  "key_questions_policy": { ... },
  "reasoning": { ... },
  "summary": { ... },
  "communication": { ... }
}
```

**Response:**
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "draft",
  "created_at": "2025-10-24T10:00:00Z"
}
```

#### GET /rubrics/{id}?version={version}
Retrieve a rubric. If version not specified, returns latest approved version.

**Response:**
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "approved",
  "created_at": "2025-10-24T10:00:00Z",
  "updated_at": "2025-10-24T11:00:00Z",
  "weights": { ... },
  ...
}
```

#### PATCH /rubrics/{id}
Apply JSON Patch operations (RFC 6902).

**Request:**
```json
{
  "operations": [
    {
      "op": "replace",
      "path": "/weights/structure",
      "value": 0.25
    },
    {
      "op": "add",
      "path": "/key_questions/-",
      "value": {
        "id": "new_question",
        "anchor": "#Q.new_question",
        "label": "New question?",
        "critical": false,
        "phrases": ["new phrase"]
      }
    }
  ]
}
```

**Response:**
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.1.0",
  "status": "draft",
  "updated_at": "2025-10-24T12:00:00Z"
}
```

#### POST /rubrics/{id}/approve
Approve a rubric version (runs QA validation first).

**Response:**
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "approved",
  "qa_report": {
    "passed": true,
    "checks": [
      {"name": "weights_sum", "passed": true},
      {"name": "critical_questions", "passed": true},
      {"name": "unique_anchors", "passed": true}
    ]
  }
}
```

### 2. Transcript Processing Service API

#### POST /transcripts/parse
Parse raw transcript into structured format.

**Request:**
```json
{
  "transcript_type": "oral" | "summary",
  "content": "00:05 So tell me what brings you in today?\n00:08 I have a headache...",
  "format": "timestamped_text"
}
```

**Response:**
```json
{
  "transcript_id": "uuid",
  "type": "oral",
  "utterances": [
    {
      "speaker": "student",
      "text": "So tell me what brings you in today?",
      "timestamp_start": "00:05",
      "timestamp_end": "00:08"
    },
    {
      "speaker": "patient",
      "text": "I have a headache",
      "timestamp_start": "00:08",
      "timestamp_end": "00:10"
    }
  ]
}
```

#### POST /transcripts/segment
Segment transcript into clinical sections.

**Request:**
```json
{
  "transcript_id": "uuid",
  "utterances": [ ... ]
}
```

**Response:**
```json
{
  "sections": [
    {
      "label": "CC",
      "utterances": [ ... ],
      "timestamp_start": "00:05",
      "timestamp_end": "00:30"
    },
    {
      "label": "HPI",
      "utterances": [ ... ],
      "timestamp_start": "00:30",
      "timestamp_end": "03:45"
    }
  ],
  "detected_order": ["CC", "HPI", "ROS", "PMH", "SH", "FH", "Summary"]
}
```

### 3. Question Matching Service API

#### POST /match/questions
Match student questions against rubric phrases.

**Request:**
```json
{
  "rubric_questions": [
    {
      "id": "onset_time",
      "anchor": "#Q.onset_time",
      "phrases": ["when did this start", "what time did you notice"]
    }
  ],
  "student_utterances": [
    {
      "text": "When did you first notice the symptoms?",
      "timestamp_start": "01:12",
      "timestamp_end": "01:15"
    }
  ],
  "matching_threshold": 0.7
}
```

**Response:**
```json
{
  "matches": [
    {
      "question_id": "onset_time",
      "question_anchor": "#Q.onset_time",
      "matched_utterance": {
        "text": "When did you first notice the symptoms?",
        "timestamp_start": "01:12",
        "timestamp_end": "01:15"
      },
      "confidence": 0.92,
      "matching_phrase": "when did this start"
    }
  ],
  "unmatched_questions": []
}
```

### 4. Structure Evaluator Service API

#### POST /evaluate/structure
Evaluate section order and completeness.

**Request:**
```json
{
  "rubric": {
    "expected_order": ["CC", "HPI", "ROS", "PMH", "SH", "FH", "Summary"],
    "penalties": [ ... ]
  },
  "detected_sections": {
    "detected_order": ["CC", "HPI", "PMH", "ROS", "SH", "FH"],
    "sections": [ ... ]
  }
}
```

**Response:**
```json
{
  "score": 0.65,
  "lcs_score": 0.85,
  "penalties_applied": [
    {
      "id": "swap_ros_before_pmh",
      "value": -0.2,
      "description": "ROS appears after PMH"
    }
  ],
  "violations": [
    {
      "description": "Missing summary section",
      "rubric_citations": ["rubric://stroke_v1#R.structure.penalty.missing_summary"],
      "severity": "major"
    }
  ],
  "successes": [
    {
      "description": "CC and HPI in correct order",
      "rubric_citations": ["rubric://stroke_v1#R.structure"]
    }
  ]
}
```

### 5. Reasoning Evaluator Service API

#### POST /evaluate/reasoning
Evaluate clinical reasoning patterns.

**Request:**
```json
{
  "rubric": {
    "required_links": [
      {
        "id": "acute_to_stroke",
        "anchor": "#R.reason.acute_to_stroke",
        "description": "Acute focal deficit → consider stroke",
        "pattern": "acute.*focal.*stroke"
      }
    ]
  },
  "transcript": {
    "utterances": [ ... ]
  }
}
```

**Response:**
```json
{
  "score": 0.5,
  "detected_links": [
    {
      "link_id": "acute_to_stroke",
      "link_anchor": "#R.reason.acute_to_stroke",
      "matched_text": "Given the acute onset of focal weakness, I'm concerned about stroke",
      "timestamp_start": "05:30",
      "timestamp_end": "05:35"
    }
  ],
  "missing_links": [
    {
      "link_id": "onset_to_ct",
      "link_anchor": "#R.reason.onset_to_ct",
      "description": "Time of onset → need for urgent CT"
    }
  ],
  "violations": [
    {
      "description": "Did not connect time-sensitive nature to need for urgent imaging",
      "rubric_citations": ["rubric://stroke_v1#R.reason.onset_to_ct"],
      "severity": "critical"
    }
  ]
}
```

### 6. Summary Evaluator Service API

#### POST /evaluate/summary
Evaluate summary constraints.

**Request:**
```json
{
  "rubric": {
    "max_tokens": 80,
    "overflow_divisor": 20,
    "required_elements": [
      {
        "id": "problem",
        "anchor": "#R.summary.req.problem",
        "description": "Chief complaint or problem statement"
      }
    ]
  },
  "summary_text": "This is a 65-year-old male with sudden onset left-sided weakness...",
  "summary_metadata": {
    "timestamp_start": "06:00",
    "timestamp_end": "06:45"
  }
}
```

**Response:**
```json
{
  "score": 0.75,
  "token_count": 95,
  "succinct_score": 0.625,
  "elements_score": 0.875,
  "matched_elements": ["problem", "pos2", "neg1", "leading_dx"],
  "missing_elements": ["differential"],
  "violations": [
    {
      "description": "Summary exceeds 80 tokens (95 tokens)",
      "rubric_citations": ["rubric://stroke_v1#R.summary.max_tokens"],
      "student_citations": ["student://summary#tokens=95"],
      "severity": "minor"
    }
  ]
}
```

### 7. Scoring Service API

#### POST /score/compute
Compute weighted final score.

**Request:**
```json
{
  "rubric_weights": {
    "structure": 0.2,
    "key_questions": 0.4,
    "reasoning": 0.25,
    "summary": 0.15
  },
  "component_scores": {
    "structure": 0.65,
    "key_questions": 0.80,
    "reasoning": 0.50,
    "summary": 0.75
  }
}
```

**Response:**
```json
{
  "overall_score": 0.685,
  "breakdown": {
    "structure": {
      "score": 0.65,
      "weight": 0.2,
      "contribution": 0.13
    },
    "key_questions": {
      "score": 0.80,
      "weight": 0.4,
      "contribution": 0.32
    },
    "reasoning": {
      "score": 0.50,
      "weight": 0.25,
      "contribution": 0.125
    },
    "summary": {
      "score": 0.75,
      "weight": 0.15,
      "contribution": 0.1125
    }
  }
}
```

### 8. Feedback Composer Service API

#### POST /feedback/compose
Generate natural language feedback from structured evaluation results.

**Request:**
```json
{
  "rubric_id": "stroke_v1",
  "evaluation_results": {
    "structure": { ... },
    "key_questions": { ... },
    "reasoning": { ... },
    "summary": { ... }
  },
  "overall_score": 0.685,
  "style": "constructive" | "detailed" | "concise"
}
```

**Response:**
```json
{
  "feedback": {
    "overall_summary": "You scored 68.5% on this stroke presentation. Strong question coverage, but missed key clinical reasoning connections.",
    "sections": [
      {
        "category": "structure",
        "items": [
          {
            "type": "violation",
            "text": "Your presentation was missing a summary section.",
            "citations": {
              "rubric": ["rubric://stroke_v1#R.structure.penalty.missing_summary"],
              "student": []
            }
          }
        ]
      },
      {
        "category": "reasoning",
        "items": [
          {
            "type": "violation",
            "text": "You did not connect the time-sensitive nature of symptoms to the need for urgent CT imaging.",
            "citations": {
              "rubric": ["rubric://stroke_v1#R.reason.onset_to_ct"],
              "student": []
            }
          },
          {
            "type": "success",
            "text": "Good connection between acute focal deficit and stroke consideration.",
            "citations": {
              "rubric": ["rubric://stroke_v1#R.reason.acute_to_stroke"],
              "student": ["student://oral#05:30–05:35"]
            }
          }
        ]
      }
    ]
  }
}
```

### 9. Teacher Edit Service API

#### POST /edit/parse
Parse natural language edit request into structured operations.

**Request:**
```json
{
  "rubric_id": "stroke_v1",
  "edit_request": "Increase the weight of key questions to 0.45 and decrease structure to 0.15"
}
```

**Response:**
```json
{
  "parsed_intent": {
    "operations": [
      {
        "field": "weights.key_questions",
        "action": "update",
        "old_value": 0.4,
        "new_value": 0.45
      },
      {
        "field": "weights.structure",
        "action": "update",
        "old_value": 0.2,
        "new_value": 0.15
      }
    ]
  },
  "json_patch": [
    {
      "op": "replace",
      "path": "/weights/key_questions",
      "value": 0.45
    },
    {
      "op": "replace",
      "path": "/weights/structure",
      "value": 0.15
    }
  ]
}
```

#### POST /edit/preview
Preview the effect of JSON Patch operations.

**Request:**
```json
{
  "rubric_id": "stroke_v1",
  "json_patch": [ ... ]
}
```

**Response:**
```json
{
  "preview": {
    "original": { ... },
    "modified": { ... },
    "diff": [
      {
        "path": "/weights/key_questions",
        "old": 0.4,
        "new": 0.45
      }
    ]
  },
  "qa_validation": {
    "passed": true,
    "warnings": []
  }
}
```

### 10. QA Validation Service API

#### POST /qa/validate
Run validation checks on a rubric.

**Request:**
```json
{
  "rubric": { ... }
}
```

**Response:**
```json
{
  "passed": true,
  "checks": [
    {
      "name": "weights_sum",
      "passed": true,
      "message": "Weights sum to 1.0"
    },
    {
      "name": "critical_questions",
      "passed": true,
      "message": "At least one critical question present"
    },
    {
      "name": "unique_anchors",
      "passed": true,
      "message": "All anchors are unique"
    },
    {
      "name": "summary_token_bounds",
      "passed": true,
      "message": "max_tokens (80) within bounds [40, 120]"
    },
    {
      "name": "no_duplicate_phrases",
      "passed": true,
      "message": "No duplicate phrases across questions"
    }
  ],
  "errors": [],
  "warnings": []
}
```

### 11. Grading Orchestrator Service API

#### POST /grade
Grade a complete student submission.

**Request:**
```json
{
  "rubric_id": "stroke_v1",
  "rubric_version": "1.0.0",
  "student_id": "student_123",
  "submission": {
    "oral_transcript": "00:05 So tell me what brings you in...",
    "summary_text": "This is a 65-year-old male..."
  }
}
```

**Response:**
```json
{
  "grading_id": "uuid",
  "rubric_id": "stroke_v1",
  "rubric_version": "1.0.0",
  "student_id": "student_123",
  "timestamp": "2025-10-24T14:30:00Z",
  "overall_score": 0.685,
  "component_scores": {
    "structure": 0.65,
    "key_questions": 0.80,
    "reasoning": 0.50,
    "summary": 0.75
  },
  "feedback": {
    "overall_summary": "...",
    "sections": [ ... ]
  },
  "detailed_results": {
    "structure": { ... },
    "key_questions": { ... },
    "reasoning": { ... },
    "summary": { ... }
  }
}
```

---

## Citation System

### Citation Format Specification

#### Rubric Citations
Format: `rubric://<rubric_id>#<anchor>`

Examples:
- `rubric://stroke_v1#R.structure`
- `rubric://stroke_v1#Q.onset_time`
- `rubric://stroke_v1#R.reason.acute_to_stroke`
- `rubric://stroke_v1#R.summary.req.problem`

#### Student Citations

**Oral Transcript:**
Format: `student://oral#<timestamp_start>–<timestamp_end>`

Examples:
- `student://oral#01:12–01:15`
- `student://oral#05:30–05:35`

**Summary:**
Format: `student://summary#tokens=<count>` or `student://summary#<timestamp_start>–<timestamp_end>`

Examples:
- `student://summary#tokens=95`
- `student://summary#06:00–06:45`

### Citation Requirements by Category

| Category | Rubric Citation | Student Citation | Notes |
|----------|----------------|------------------|-------|
| Structure | Required | Optional | Student citation for detected sections |
| Key Questions | Required | Required for matches | Must cite matched utterance timestamp |
| Reasoning | Required | Required | Dual citation rule - both required |
| Summary | Required | Required | Token count or timestamp |
| Communication | Required | Optional | For MVP, weight=0 |

### Citation Validation Rules

1. **Every feedback item must have at least one rubric citation**
2. **Rubric citations must reference valid anchors in the rubric**
3. **Student citations must use valid timestamp format (MM:SS or HH:MM:SS)**
4. **Reasoning violations must have both rubric AND student citations**
5. **Question matches must cite the specific utterance timestamp**

---

## Implementation Notes

### Technology Stack

#### Backend Services
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, high performance, auto-generated OpenAPI docs)
- **Validation**: Pydantic v2 (data validation and serialization)
- **Testing**: pytest + pytest-asyncio
- **Containerization**: Docker + Docker Compose

#### Algorithms & Libraries
- **Question Matching**:
  - BM25: `rank-bm25` library
  - Embeddings: `sentence-transformers` (all-MiniLM-L6-v2 model)
  - Similarity: cosine similarity via `scikit-learn`
- **LCS Algorithm**: Custom implementation or `difflib.SequenceMatcher`
- **JSON Patch**: `jsonpatch` library (RFC 6902 compliant)
- **NLP (Teacher Edit)**: `spaCy` or OpenAI API for intent parsing

#### Storage
- **Rubrics**: JSON files in `/data/rubrics/` directory (versioned)
- **Grading Results**: JSON files in `/data/results/` directory
- **Future**: PostgreSQL or MongoDB for production

#### API Gateway
- **Option 1**: Nginx reverse proxy
- **Option 2**: Kong API Gateway
- **Option 3**: AWS API Gateway (for cloud deployment)

### Directory Structure
```
med-ed-op-grader/
├── services/
│   ├── rubric_management/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── routes.py
│   │   │   └── storage.py
│   │   └── tests/
│   ├── transcript_processing/
│   ├── question_matching/
│   ├── structure_evaluator/
│   ├── reasoning_evaluator/
│   ├── summary_evaluator/
│   ├── scoring/
│   ├── feedback_composer/
│   ├── teacher_edit/
│   ├── qa_validation/
│   └── grading_orchestrator/
├── shared/
│   ├── models/          # Shared Pydantic models
│   ├── utils/           # Shared utilities
│   └── schemas/         # JSON schemas
├── data/
│   ├── rubrics/         # Rubric JSON files
│   ├── results/         # Grading results
│   └── examples/        # Example transcripts
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── tests/
│   └── integration/     # Integration tests
├── docs/
│   └── api/             # API documentation
├── SYSTEM_GUIDE.md
└── README.md
```

### Development Workflow

1. **Local Development**:
   - Each service runs independently on different ports
   - Use `docker-compose up` to start all services
   - Hot reload enabled for development

2. **Testing**:
   - Unit tests for each service
   - Integration tests for service interactions
   - End-to-end tests for complete grading workflow

3. **CI/CD Pipeline**:
   - GitHub Actions for automated testing
   - Build Docker images on merge to main
   - Deploy to staging environment
   - Manual approval for production deployment

### Error Handling Strategy

1. **Service-Level Errors**:
   - Return HTTP status codes: 400 (bad request), 404 (not found), 500 (internal error)
   - Include error details in response body
   - Log errors with context

2. **Orchestrator Error Handling**:
   - If a service fails, return partial results with error indication
   - Retry transient failures (network issues)
   - Fail fast for validation errors

3. **Citation Validation**:
   - Validate all citations before returning feedback
   - Reject feedback items without proper citations
   - Log citation validation failures

### Performance Considerations

1. **Parallel Evaluation**:
   - Structure, Questions, Reasoning, Summary evaluators run in parallel
   - Use asyncio for concurrent API calls

2. **Caching**:
   - Cache rubrics in memory (invalidate on update)
   - Cache embeddings for question phrases
   - Cache LCS computations for common sequences

3. **Scalability**:
   - Each service can scale independently
   - Stateless services (no session state)
   - Use message queue (RabbitMQ/Redis) for async processing if needed

---

## Decision Log

### Decision 1: FastAPI over Flask
**Date**: 2025-10-24
**Rationale**: FastAPI provides async support, automatic OpenAPI documentation, built-in validation with Pydantic, and better performance. Essential for microservices architecture.

### Decision 2: JSON File Storage for MVP
**Date**: 2025-10-24
**Rationale**: Simplifies initial development. Rubrics are versioned files in `/data/rubrics/`. Easy to migrate to database later. Git-friendly for version control.

### Decision 3: BM25 + Embeddings for Question Matching
**Date**: 2025-10-24
**Rationale**: BM25 handles exact phrase matching well. Embeddings capture semantic similarity. Hybrid approach balances precision and recall.

### Decision 4: Dual Citation Rule for Reasoning
**Date**: 2025-10-24
**Rationale**: Prevents hallucination. Reasoning feedback must cite both rubric anchor (what's expected) and student span (what was said/missing).

### Decision 5: LCS for Structure Scoring
**Date**: 2025-10-24
**Rationale**: Longest Common Subsequence naturally handles partial order matches. Robust to missing or extra sections. Mathematically sound.

### Decision 6: Separate Scoring Service
**Date**: 2025-10-24
**Rationale**: Centralizes formula application. Makes it easy to adjust weights or formulas without touching evaluators. Single source of truth for scoring logic.

### Decision 7: Template-Based Feedback Composition
**Date**: 2025-10-24
**Rationale**: For MVP, use templates to generate feedback. LLM rephrasing is optional enhancement. Ensures deterministic, citation-backed feedback.

### Decision 8: RFC 6902 JSON Patch for Edits
**Date**: 2025-10-24
**Rationale**: Standard format for JSON modifications. Well-supported libraries. Atomic operations. Easy to preview and validate.

### Decision 9: Grading Orchestrator Pattern
**Date**: 2025-10-24
**Rationale**: Centralized workflow coordination. Handles service dependencies. Simplifies client integration (single API call to grade).

### Decision 10: QA Validation as Separate Service
**Date**: 2025-10-24
**Rationale**: Reusable across rubric creation, editing, and approval workflows. Can be enhanced independently. Clear separation of concerns.

---

## Example Rubrics

### Stroke V1 Rubric (Abbreviated)
```json
{
  "rubric_id": "stroke_v1",
  "version": "1.0.0",
  "status": "approved",
  "weights": {
    "structure": 0.2,
    "key_questions": 0.4,
    "reasoning": 0.25,
    "summary": 0.15,
    "communication": 0.0
  },
  "structure": {
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
  "key_questions": [
    {
      "id": "onset_time",
      "anchor": "#Q.onset_time",
      "label": "When did symptoms start? (Last known well)",
      "critical": true,
      "phrases": [
        "when did this start",
        "what time did you notice",
        "when were you last normal",
        "last known well"
      ]
    },
    {
      "id": "focal_symptoms",
      "anchor": "#Q.focal_symptoms",
      "label": "Which specific functions are affected?",
      "critical": true,
      "phrases": [
        "which side is weak",
        "can you move your arm",
        "facial droop",
        "speech difficulty"
      ]
    }
  ],
  "key_questions_policy": {
    "anchor": "#R.key_questions",
    "critical_weight": 2.0,
    "noncritical_weight": 1.0,
    "coverage_threshold": 0.7
  },
  "reasoning": {
    "anchor": "#R.reasoning",
    "required_links": [
      {
        "id": "acute_to_stroke",
        "anchor": "#R.reason.acute_to_stroke",
        "description": "Acute focal deficit → consider stroke",
        "pattern": "acute.*focal.*(stroke|CVA)|stroke.*acute.*deficit"
      },
      {
        "id": "onset_to_ct",
        "anchor": "#R.reason.onset_to_ct",
        "description": "Time of onset → need for urgent CT",
        "pattern": "(time|onset).*(CT|imaging|scan)|(CT|imaging).*(urgent|immediate|stat)"
      }
    ],
    "major_gap_penalty": -0.5
  },
  "summary": {
    "anchor": "#R.summary",
    "max_tokens": 80,
    "overflow_divisor": 20,
    "required_elements": [
      {
        "id": "problem",
        "anchor": "#R.summary.req.problem",
        "description": "Chief complaint or problem statement",
        "pattern": "(year.old|y/o).*(male|female|patient)"
      },
      {
        "id": "pos2",
        "anchor": "#R.summary.req.pos2",
        "description": "At least 2 positive findings",
        "pattern": null
      },
      {
        "id": "leading_dx",
        "anchor": "#R.summary.req.leading_dx",
        "description": "Leading diagnosis",
        "pattern": "(concern|worried|suspect|likely|diagnosis).*(stroke|CVA)"
      }
    ]
  },
  "communication": {
    "anchor": "#R.communication",
    "weight": 0.0,
    "rules": []
  }
}
```

---

## Next Steps

### Phase 1: MVP Core (Current)
- [x] Create SYSTEM_GUIDE.md
- [ ] Set up project structure
- [ ] Implement Rubric Management Service
- [ ] Implement Structure Evaluator Service
- [ ] Implement Question Matching Service
- [ ] Implement Scoring Service
- [ ] Implement Feedback Composer Service
- [ ] Create Docker containers
- [ ] Set up basic CI/CD

### Phase 2: Enhancement
- [ ] Reasoning Evaluator Service
- [ ] Summary Evaluator Service
- [ ] Teacher Edit Service
- [ ] QA Validation Service
- [ ] Advanced embedding-based matching
- [ ] Integration tests

### Phase 3: Deployment
- [ ] AWS deployment configuration
- [ ] Production CI/CD pipeline
- [ ] Monitoring and logging
- [ ] Performance optimization

---

## Appendix: Full Example Rubrics

See `/data/rubrics/examples/` for complete rubric JSON files:
- `stroke_v1.json` - Stroke presentation rubric
- `chest_pain_v1.json` - Chest pain presentation rubric

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-24
**Maintained By**: Development Team





