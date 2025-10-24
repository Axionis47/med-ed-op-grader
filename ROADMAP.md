# Development Roadmap

## Medical Education Oral Presentation Grading System

---

## ✅ Phase 1: MVP Core (COMPLETE)

**Status**: Complete  
**Duration**: Initial implementation  
**Completion Date**: 2025-10-24

### Deliverables
- [x] System architecture and documentation (SYSTEM_GUIDE.md)
- [x] Shared models and utilities
- [x] Rubric Management Service
- [x] Structure Evaluator Service
- [x] Scoring Service
- [x] Feedback Composer Service
- [x] Docker containerization
- [x] CI/CD pipeline (GitHub Actions)
- [x] Example rubrics (stroke_v1, chest_pain_v1)
- [x] Test demonstration script

---

## 🚧 Phase 2: Enhancement Services (NEXT)

**Status**: Not Started  
**Estimated Duration**: 2-3 weeks  
**Priority**: High

### 2.1 Transcript Processing Service (Week 1)

**Port**: 8002  
**Priority**: Critical

#### Tasks
- [ ] Implement transcript parser
  - Parse timestamped text format
  - Extract utterances with speaker identification
  - Handle multiple timestamp formats (MM:SS, HH:MM:SS)
  
- [ ] Implement section segmentation
  - Detect section boundaries using keywords
  - Label sections (CC, HPI, ROS, PMH, SH, FH, Summary)
  - Handle ambiguous cases
  
- [ ] Create API endpoints
  - `POST /transcripts/parse` - Parse raw transcript
  - `POST /transcripts/segment` - Segment into sections
  
- [ ] Write tests
  - Unit tests for parser
  - Integration tests with sample transcripts
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: None  
**Estimated Effort**: 3-4 days

---

### 2.2 Question Matching Service (Week 1-2)

**Port**: 8003  
**Priority**: Critical

#### Tasks
- [ ] Implement BM25 phrase matching
  - Install and configure `rank-bm25` library
  - Index rubric phrases
  - Compute BM25 scores
  
- [ ] Implement embedding-based matching
  - Install `sentence-transformers`
  - Load model (all-MiniLM-L6-v2)
  - Compute semantic similarity
  
- [ ] Implement hybrid matching
  - Combine BM25 and embedding scores
  - Tune matching threshold
  - Handle edge cases
  
- [ ] Create API endpoints
  - `POST /match/questions` - Match questions
  
- [ ] Write tests
  - Test with example questions
  - Validate confidence scores
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: None  
**Estimated Effort**: 4-5 days

---

### 2.3 Reasoning Evaluator Service (Week 2)

**Port**: 8005  
**Priority**: High

#### Tasks
- [ ] Implement pattern matching
  - Regex-based link detection
  - Context window extraction
  - Timestamp capture
  
- [ ] Implement dual citation validation
  - Ensure both rubric and student citations
  - Reject feedback without both
  
- [ ] Create API endpoints
  - `POST /evaluate/reasoning` - Evaluate reasoning
  
- [ ] Write tests
  - Test with example reasoning patterns
  - Validate dual citations
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: Transcript Processing Service  
**Estimated Effort**: 3-4 days

---

### 2.4 Summary Evaluator Service (Week 2)

**Port**: 8006  
**Priority**: High

#### Tasks
- [ ] Implement token counting
  - Use advanced tokenizer from shared utils
  - Handle edge cases (hyphenated words, contractions)
  
- [ ] Implement element detection
  - Pattern matching for required elements
  - Count positive/negative findings
  - Detect leading diagnosis
  
- [ ] Implement scoring formulas
  - Succinctness score (token-based)
  - Elements score (coverage-based)
  - Combined score (50/50 split)
  
- [ ] Create API endpoints
  - `POST /evaluate/summary` - Evaluate summary
  
- [ ] Write tests
  - Test with example summaries
  - Validate scoring formulas
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: Transcript Processing Service  
**Estimated Effort**: 3-4 days

---

### 2.5 QA Validation Service (Week 3)

**Port**: 8010  
**Priority**: Medium

#### Tasks
- [ ] Implement validation checks
  - Weights sum to 1.0
  - At least one critical question
  - Unique anchors
  - Token bounds (40-120)
  - No duplicate phrases
  
- [ ] Create API endpoints
  - `POST /qa/validate` - Validate rubric
  
- [ ] Integrate with Rubric Management
  - Call QA validation before approval
  - Return detailed validation report
  
- [ ] Write tests
  - Test each validation rule
  - Test with invalid rubrics
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: None  
**Estimated Effort**: 2-3 days

---

### 2.6 Teacher Edit Service (Week 3)

**Port**: 8009  
**Priority**: Medium

#### Tasks
- [ ] Implement NLP parsing
  - Use spaCy or OpenAI API
  - Extract intent from natural language
  - Map to JSON Patch operations
  
- [ ] Implement JSON Patch generation
  - Generate RFC 6902 operations
  - Validate operations
  
- [ ] Create API endpoints
  - `POST /edit/parse` - Parse edit request
  - `POST /edit/preview` - Preview changes
  
- [ ] Write tests
  - Test with example edit requests
  - Validate JSON Patch generation
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: QA Validation Service  
**Estimated Effort**: 3-4 days

---

### 2.7 Grading Orchestrator Service (Week 3)

**Port**: 8000  
**Priority**: Critical

#### Tasks
- [ ] Implement workflow coordination
  - Fetch rubric from Rubric Management
  - Parse transcript via Transcript Processing
  - Parallel evaluation (Structure, Questions, Reasoning, Summary)
  - Aggregate scores via Scoring Service
  - Generate feedback via Feedback Composer
  
- [ ] Implement error handling
  - Retry transient failures
  - Return partial results on service failure
  - Log errors with context
  
- [ ] Create API endpoints
  - `POST /grade` - Grade submission
  
- [ ] Write tests
  - End-to-end grading workflow
  - Error handling scenarios
  
- [ ] Create Dockerfile and add to docker-compose

**Dependencies**: All other services  
**Estimated Effort**: 4-5 days

---

### 2.8 Integration Testing (Week 3)

**Priority**: High

#### Tasks
- [ ] Create integration test suite
  - Test service interactions
  - Test complete grading workflow
  - Test error scenarios
  
- [ ] Create example transcripts
  - Stroke presentation transcript
  - Chest pain presentation transcript
  - Edge cases (missing sections, etc.)
  
- [ ] Validate end-to-end grading
  - Load rubric
  - Parse transcript
  - Evaluate all components
  - Compute score
  - Generate feedback
  - Verify citations
  
- [ ] Add to CI/CD pipeline

**Dependencies**: All services  
**Estimated Effort**: 3-4 days

---

## 🚀 Phase 3: Deployment & Production (FUTURE)

**Status**: Not Started  
**Estimated Duration**: 2-3 weeks  
**Priority**: Medium

### 3.1 AWS Deployment

#### Tasks
- [ ] Set up AWS infrastructure
  - ECS/Fargate for containers
  - Application Load Balancer
  - RDS or DocumentDB for storage
  - S3 for rubric backups
  
- [ ] Configure networking
  - VPC and subnets
  - Security groups
  - NAT gateway
  
- [ ] Set up CI/CD for AWS
  - Deploy on merge to main
  - Blue-green deployment
  - Rollback capability
  
- [ ] Configure monitoring
  - CloudWatch logs and metrics
  - Alarms for service health
  - Dashboard for system overview

**Estimated Effort**: 1-2 weeks

---

### 3.2 Production Enhancements

#### Tasks
- [ ] Database migration
  - Migrate from JSON files to PostgreSQL/MongoDB
  - Implement connection pooling
  - Add indexes for performance
  
- [ ] Caching layer
  - Redis for rubric caching
  - Cache embeddings for questions
  - Cache LCS computations
  
- [ ] Performance optimization
  - Profile services
  - Optimize hot paths
  - Add request batching
  
- [ ] Security enhancements
  - Authentication and authorization
  - API rate limiting
  - Input validation and sanitization
  - HTTPS/TLS

**Estimated Effort**: 1-2 weeks

---

### 3.3 Monitoring & Observability

#### Tasks
- [ ] Set up Prometheus
  - Metrics collection
  - Service health metrics
  - Custom business metrics
  
- [ ] Set up Grafana
  - Dashboards for each service
  - Overall system dashboard
  - Alerting rules
  
- [ ] Distributed tracing
  - OpenTelemetry integration
  - Trace grading workflows
  - Identify bottlenecks
  
- [ ] Log aggregation
  - Centralized logging (ELK or CloudWatch)
  - Structured logging
  - Log retention policies

**Estimated Effort**: 1 week

---

## 🔮 Phase 4: Advanced Features (FUTURE)

**Status**: Not Started  
**Priority**: Low

### Potential Features
- [ ] LLM-based feedback rephrasing
  - Optional enhancement to template-based feedback
  - Maintain citation requirements
  
- [ ] Real-time grading
  - WebSocket support
  - Live feedback during presentation
  
- [ ] Multi-language support
  - Internationalization (i18n)
  - Support for non-English presentations
  
- [ ] Advanced analytics
  - Student performance trends
  - Rubric effectiveness analysis
  - Question difficulty analysis
  
- [ ] Teacher dashboard
  - Rubric management UI
  - Student performance visualization
  - Bulk grading operations
  
- [ ] Student portal
  - View feedback
  - Track progress
  - Practice mode

---

## 📊 Success Metrics

### Phase 2 Goals
- All 7 remaining services implemented
- 100% test coverage for new services
- End-to-end grading workflow functional
- All feedback items have valid citations
- Scoring is reproducible (same input → same output)

### Phase 3 Goals
- System deployed to AWS
- 99.9% uptime
- < 2 second response time for grading
- Monitoring and alerting operational

### Phase 4 Goals
- Advanced features based on user feedback
- Scalability to 1000+ concurrent users
- Support for 10+ different presentation types

---

## 🎯 Current Focus

**Immediate Next Steps** (Week 1):
1. Implement Transcript Processing Service
2. Implement Question Matching Service
3. Begin Reasoning Evaluator Service

**Review Points**:
- End of Week 1: Review Transcript Processing and Question Matching
- End of Week 2: Review all evaluator services
- End of Week 3: Review orchestrator and integration tests

---

## 📝 Notes

- Maintain SYSTEM_GUIDE.md as services are added
- Update docker-compose.yml for each new service
- Add API documentation examples to README.md
- Keep test coverage above 80%
- Follow citation-gated feedback principle strictly

---

**Last Updated**: 2025-10-24  
**Next Review**: Start of Phase 2

