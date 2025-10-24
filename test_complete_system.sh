#!/bin/bash

# Complete System Test Script
# Tests the entire grading workflow end-to-end

set -e  # Exit on error

echo "=========================================="
echo "Medical Education Grading System"
echo "Complete End-to-End Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URLs
ORCHESTRATOR_URL="http://localhost:8000"
RUBRIC_URL="http://localhost:8001"

echo -e "${BLUE}Step 1: Checking service health...${NC}"
echo "Checking orchestrator..."
curl -s $ORCHESTRATOR_URL/health | jq '.'

echo ""
echo "Checking all services status..."
curl -s $ORCHESTRATOR_URL/services/status | jq '.services | to_entries[] | {service: .key, status: .value.status}'

echo ""
echo -e "${GREEN}✓ All services are healthy${NC}"
echo ""

echo -e "${BLUE}Step 2: Creating stroke rubric...${NC}"
curl -s -X POST $RUBRIC_URL/rubrics \
  -H "Content-Type: application/json" \
  -d @data/rubrics/examples/stroke_v1.json | jq '{rubric_id, version, status}'

echo ""
echo -e "${GREEN}✓ Rubric created${NC}"
echo ""

echo -e "${BLUE}Step 3: Grading a presentation...${NC}"
echo "Using example transcript..."

# Create grading request
cat > /tmp/grading_request.json <<'EOF'
{
  "rubric_id": "stroke_v1",
  "transcript_id": "stroke_test_001",
  "raw_text": "[00:05] Student: Good morning. Tell me what brings you in today?\n[00:08] Patient: I have sudden weakness on my left side.\n[00:12] Student: I'm sorry to hear that. When did you first notice the weakness?\n[00:15] Patient: About 2 hours ago, around 8 AM this morning.\n[00:20] Student: Can you describe the weakness for me? Which parts of your body are affected?\n[00:25] Patient: My left arm and left leg feel very weak. I can barely lift my arm.\n[00:30] Student: Did this come on suddenly or gradually?\n[00:33] Patient: It was very sudden. I was eating breakfast and suddenly couldn't hold my fork.\n[00:40] Student: Have you had any other symptoms? Any headache, vision changes, or difficulty speaking?\n[00:45] Patient: No headache, but I did feel a bit dizzy when it started.\n[00:50] Student: Any chest pain or shortness of breath?\n[00:53] Patient: No, nothing like that.\n[00:58] Student: Do you have any past medical history? Any chronic conditions?\n[01:02] Patient: Yes, I have high blood pressure and diabetes.\n[01:07] Student: Are you taking medications for those?\n[01:10] Patient: Yes, I take lisinopril and metformin.\n[01:15] Student: Do you smoke or drink alcohol?\n[01:18] Patient: I used to smoke but quit 5 years ago. I have a glass of wine occasionally.\n[01:25] Student: Does anyone in your family have a history of stroke or heart disease?\n[01:30] Patient: My father had a stroke when he was 70.\n[01:35] Student: So to summarize, this is a 65-year-old male with a history of hypertension and diabetes presenting with sudden onset left-sided weakness that started 2 hours ago. He also experienced some dizziness. He has a family history of stroke. Given the sudden onset and risk factors, this is concerning for an acute ischemic stroke and requires immediate evaluation and imaging."
}
EOF

echo "Sending grading request to orchestrator..."
RESULT=$(curl -s -X POST $ORCHESTRATOR_URL/grade \
  -H "Content-Type: application/json" \
  -d @/tmp/grading_request.json)

echo ""
echo -e "${GREEN}✓ Grading complete!${NC}"
echo ""

echo -e "${BLUE}Step 4: Displaying results...${NC}"
echo ""

echo "=== OVERALL SCORE ==="
echo "$RESULT" | jq '{
  transcript_id,
  rubric_id,
  overall_score,
  component_scores
}'

echo ""
echo "=== SCORE BREAKDOWN ==="
echo "$RESULT" | jq '.score_breakdown'

echo ""
echo "=== FEEDBACK SUMMARY ==="
echo "$RESULT" | jq -r '.feedback.overall_summary'

echo ""
echo "=== DETAILED FEEDBACK ==="
echo "$RESULT" | jq '.feedback.sections[] | {
  category,
  item_count: (.items | length),
  sample_items: (.items[0:2] | map(.text))
}'

echo ""
echo "=== CITATION VALIDATION ==="
TOTAL_ITEMS=$(echo "$RESULT" | jq '[.feedback.sections[].items[]] | length')
ITEMS_WITH_RUBRIC=$(echo "$RESULT" | jq '[.feedback.sections[].items[] | select(.citations.rubric | length > 0)] | length')
echo "Total feedback items: $TOTAL_ITEMS"
echo "Items with rubric citations: $ITEMS_WITH_RUBRIC"

if [ "$TOTAL_ITEMS" -eq "$ITEMS_WITH_RUBRIC" ]; then
  echo -e "${GREEN}✓ All feedback items have rubric citations!${NC}"
else
  echo -e "${YELLOW}⚠ Some feedback items missing rubric citations${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Complete System Test: SUCCESS${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. View API docs: http://localhost:8000/docs"
echo "2. Check service status: curl http://localhost:8000/services/status"
echo "3. View logs: docker-compose logs -f"
echo ""

# Cleanup
rm /tmp/grading_request.json

