"""
QA Validation Service

This service validates rubrics before approval to ensure:
1. Weights sum to 1.0
2. At least one critical question exists
3. All anchors are unique
4. Token bounds are reasonable
5. No duplicate phrases

Port: 8010
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import Rubric
from services.qa_validation.app.validator import RubricValidator

app = FastAPI(
    title="QA Validation Service",
    description="Validate rubrics for quality assurance before approval",
    version="1.0.0"
)


# Request/Response Models
class ValidateRequest(BaseModel):
    """Request to validate a rubric."""
    rubric: Rubric = Field(..., description="Rubric to validate")


class ValidationResult(BaseModel):
    """Validation result."""
    is_valid: bool = Field(..., description="Whether the rubric is valid")
    error_count: int = Field(..., description="Number of errors")
    warning_count: int = Field(..., description="Number of warnings")
    errors: list[dict] = Field(default_factory=list, description="List of errors")
    warnings: list[dict] = Field(default_factory=list, description="List of warnings")
    all_issues: list[dict] = Field(default_factory=list, description="All issues (errors + warnings)")


# Initialize validator
validator = RubricValidator()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "qa_validation"
    }


@app.post("/qa/validate", response_model=ValidationResult)
async def validate_rubric(request: ValidateRequest):
    """
    Validate a rubric for quality assurance.
    
    Checks performed:
    1. **Weights**: Must sum to 1.0 (±0.001 tolerance)
    2. **Critical Questions**: At least one must exist
    3. **Unique Anchors**: All anchors must be unique
    4. **Token Bounds**: min_tokens < max_tokens, reasonable ranges
    5. **Duplicate Phrases**: Warns if duplicate phrases exist
    6. **Question Phrases**: All questions must have at least one phrase
    
    Returns:
    - is_valid: True if no errors (warnings are allowed)
    - error_count: Number of errors found
    - warning_count: Number of warnings found
    - errors: List of error details
    - warnings: List of warning details
    - all_issues: Combined list of all issues
    """
    try:
        result = validator.validate(request.rubric)
        return ValidationResult(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to validate rubric: {str(e)}")


@app.get("/qa/rules")
async def get_validation_rules():
    """
    Get the validation rules applied by this service.
    
    Returns a description of all validation checks performed.
    """
    return {
        "rules": [
            {
                "name": "Weights Sum",
                "severity": "error",
                "description": "All component weights must sum to 1.0 (±0.001 tolerance)"
            },
            {
                "name": "Non-negative Weights",
                "severity": "error",
                "description": "All weights must be non-negative"
            },
            {
                "name": "Critical Questions",
                "severity": "error",
                "description": "At least one critical question must be defined"
            },
            {
                "name": "Unique Anchors",
                "severity": "error",
                "description": "All anchors must be unique across the rubric"
            },
            {
                "name": "Token Bounds Order",
                "severity": "error",
                "description": "min_tokens must be less than max_tokens"
            },
            {
                "name": "Token Bounds Range",
                "severity": "warning",
                "description": "Recommended: min_tokens >= 40, max_tokens <= 120"
            },
            {
                "name": "Duplicate Phrases",
                "severity": "warning",
                "description": "Warns if duplicate phrases exist across questions"
            },
            {
                "name": "Question Phrases",
                "severity": "error",
                "description": "All questions must have at least one phrase"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

