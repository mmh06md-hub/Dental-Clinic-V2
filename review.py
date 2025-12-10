"""
Review Model

This module defines the Review class for patient feedback on doctors
and the dental clinic experience.

Features:
- Star rating (1-5)
- Text reviews with validation
- Anonymous reviews option
- Timestamp tracking
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


class Review(BaseModel):
    """
    Review model representing patient feedback.
    
    Attributes:
        id: Unique review identifier
        patient_name: Name of reviewer
        doctor_name: Name of reviewed doctor
        rating: Star rating (1-5)
        comment: Text review
        is_anonymous: Whether reviewer name is hidden
        created_at: When review was posted
        helpful_count: Number of times marked as helpful
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8], alias="_id")
    patient_name: str = Field(..., min_length=1, max_length=100)
    doctor_name: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=5, max_length=1000)
    is_anonymous: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    helpful_count: int = Field(default=0, ge=0)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Ensure rating is valid."""
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError('Rating must be an integer between 1 and 5')
        return v

    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v):
        """Ensure comment is meaningful."""
        if not v.strip():
            raise ValueError('Comment cannot be empty')
        # Remove extra whitespace
        return v.strip()

    def __str__(self) -> str:
        """String representation."""
        stars = "⭐" * self.rating
        reviewer = "Anonymous" if self.is_anonymous else self.patient_name
        return f"{stars} by {reviewer}: {self.comment[:50]}..."

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Review({self.id}, {self.rating}/5)"

    def mark_helpful(self) -> int:
        """Increment helpful count."""
        self.helpful_count += 1
        return self.helpful_count
