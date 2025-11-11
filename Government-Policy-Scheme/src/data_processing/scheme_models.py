"""
Scheme Data Models
Pydantic models for government scheme data structure
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class SchemeCategory(str, Enum):
    """Scheme categories"""
    EDUCATION = "Education & Scholarships"
    AGRICULTURE = "Agriculture & Farming"
    BUSINESS = "Business & Entrepreneurship"
    HOUSING = "Housing & Infrastructure"
    HEALTHCARE = "Healthcare"
    WOMEN = "Women Empowerment"
    SENIOR_CITIZENS = "Senior Citizens"
    EMPLOYMENT = "Employment & Skill Development"
    FINANCIAL = "Financial Assistance"
    SOCIAL_WELFARE = "Social Welfare"
    OTHER = "Other"


class EligibilityGender(str, Enum):
    """Gender options"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    ALL = "All"


class EligibilityCategory(str, Enum):
    """Social category"""
    GENERAL = "General"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"
    ALL = "All"


class BenefitType(str, Enum):
    """Type of benefit"""
    SUBSIDY = "Subsidy"
    LOAN = "Loan"
    GRANT = "Grant"
    SCHOLARSHIP = "Scholarship"
    PENSION = "Pension"
    INSURANCE = "Insurance"
    TRAINING = "Training"
    TAX_BENEFIT = "Tax Benefit"
    OTHER = "Other"


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for a scheme"""
    min_age: Optional[int] = Field(None, description="Minimum age requirement")
    max_age: Optional[int] = Field(None, description="Maximum age requirement")
    gender: List[EligibilityGender] = Field(
        default=[EligibilityGender.ALL],
        description="Eligible genders"
    )
    category: List[EligibilityCategory] = Field(
        default=[EligibilityCategory.ALL],
        description="Eligible social categories"
    )
    min_income: Optional[float] = Field(None, description="Minimum annual income")
    max_income: Optional[float] = Field(None, description="Maximum annual income")
    states: List[str] = Field(
        default=[],
        description="Applicable states (empty = all India)"
    )
    occupation: List[str] = Field(
        default=[],
        description="Eligible occupations (empty = all)"
    )
    education: List[str] = Field(
        default=[],
        description="Education requirements (empty = any)"
    )
    marital_status: List[str] = Field(
        default=[],
        description="Marital status requirement (empty = any)"
    )
    disability: Optional[bool] = Field(None, description="Disability requirement")
    bpl_card: Optional[bool] = Field(None, description="BPL card requirement")
    rural_area: Optional[bool] = Field(None, description="Rural area requirement")
    custom_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom criteria"
    )

    @validator('min_age', 'max_age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 120):
            raise ValueError("Age must be between 0 and 120")
        return v

    @validator('max_income')
    def validate_income(cls, v, values):
        if v is not None and v < 0:
            raise ValueError("Income cannot be negative")
        if 'min_income' in values and values['min_income'] is not None:
            if v < values['min_income']:
                raise ValueError("Maximum income must be >= minimum income")
        return v


class BenefitDetails(BaseModel):
    """Details of scheme benefits"""
    benefit_type: List[BenefitType] = Field(
        default=[BenefitType.OTHER],
        description="Type of benefits"
    )
    amount: Optional[float] = Field(None, description="Benefit amount in INR")
    amount_min: Optional[float] = Field(None, description="Minimum benefit amount")
    amount_max: Optional[float] = Field(None, description="Maximum benefit amount")
    description: str = Field(..., description="Benefit description")
    duration: Optional[str] = Field(None, description="Benefit duration")
    is_recurring: bool = Field(False, description="Is benefit recurring")


class DocumentRequired(BaseModel):
    """Required documents for application"""
    name: str = Field(..., description="Document name")
    is_mandatory: bool = Field(True, description="Is document mandatory")
    description: Optional[str] = Field(None, description="Document description")


class ApplicationProcess(BaseModel):
    """Application process details"""
    mode: List[str] = Field(
        default=["Online"],
        description="Application modes (Online, Offline, Both)"
    )
    steps: List[str] = Field(default_factory=list, description="Application steps")
    website: Optional[str] = Field(None, description="Application website URL")
    helpline: Optional[str] = Field(None, description="Helpline number")
    processing_time: Optional[str] = Field(None, description="Expected processing time")


class GovernmentScheme(BaseModel):
    """Complete government scheme model"""
    scheme_id: str = Field(..., description="Unique scheme identifier")
    name: str = Field(..., description="Scheme name")
    ministry: str = Field(..., description="Ministry/Department")
    category: List[SchemeCategory] = Field(..., description="Scheme categories")
    description: str = Field(..., description="Scheme description")

    # Eligibility
    eligibility: EligibilityCriteria = Field(..., description="Eligibility criteria")

    # Benefits
    benefits: BenefitDetails = Field(..., description="Benefit details")

    # Application
    documents_required: List[DocumentRequired] = Field(
        default_factory=list,
        description="Required documents"
    )
    application_process: ApplicationProcess = Field(
        ...,
        description="Application process"
    )

    # Metadata
    source_url: Optional[str] = Field(None, description="Source URL")
    source_document: Optional[str] = Field(None, description="Source document path")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last updated timestamp"
    )
    is_active: bool = Field(True, description="Is scheme currently active")
    launch_date: Optional[datetime] = Field(None, description="Scheme launch date")
    end_date: Optional[datetime] = Field(None, description="Scheme end date")

    # Additional info
    tags: List[str] = Field(default_factory=list, description="Search tags")
    related_schemes: List[str] = Field(
        default_factory=list,
        description="Related scheme IDs"
    )
    success_stories: List[str] = Field(
        default_factory=list,
        description="Success stories/testimonials"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scheme_id": "PM-KISAN-2024",
                "name": "PM-KISAN Samman Nidhi",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "category": ["Agriculture & Farming", "Financial Assistance"],
                "description": "Direct income support to farmers",
                "eligibility": {
                    "min_age": 18,
                    "occupation": ["Farmer"],
                    "max_income": None,
                },
                "benefits": {
                    "benefit_type": ["Grant"],
                    "amount": 6000,
                    "description": "₹6000 per year in three installments",
                    "is_recurring": True,
                },
                "documents_required": [
                    {"name": "Aadhaar Card", "is_mandatory": True},
                    {"name": "Bank Account Details", "is_mandatory": True},
                    {"name": "Land Ownership Document", "is_mandatory": True},
                ],
                "application_process": {
                    "mode": ["Online", "Offline"],
                    "website": "https://pmkisan.gov.in",
                    "helpline": "155261",
                },
            }
        }

    def to_vector_metadata(self) -> Dict[str, Any]:
        """
        Convert scheme to metadata format for vector database

        Returns:
            Dictionary suitable for vector DB storage
        """
        return {
            'scheme_id': self.scheme_id,
            'name': self.name,
            'ministry': self.ministry,
            'category': [cat.value for cat in self.category],
            'description': self.description,
            'benefit_amount_min': self.benefits.amount_min or self.benefits.amount or 0,
            'benefit_amount_max': self.benefits.amount_max or self.benefits.amount or 0,
            'min_age': self.eligibility.min_age,
            'max_age': self.eligibility.max_age,
            'gender': [g.value for g in self.eligibility.gender],
            'social_category': [c.value for c in self.eligibility.category],
            'min_income': self.eligibility.min_income,
            'max_income': self.eligibility.max_income,
            'states': self.eligibility.states,
            'occupation': self.eligibility.occupation,
            'website': self.application_process.website,
            'is_active': self.is_active,
            'tags': self.tags,
            # Full text for search
            'content': self._generate_searchable_content(),
        }

    def _generate_searchable_content(self) -> str:
        """Generate full searchable text content"""
        parts = [
            self.name,
            self.description,
            self.ministry,
            self.benefits.description,
            ' '.join(self.tags),
            ' '.join([cat.value for cat in self.category]),
        ]
        return ' '.join(filter(None, parts))


class UserProfile(BaseModel):
    """User profile for eligibility matching"""
    age: int = Field(..., ge=0, le=120)
    gender: EligibilityGender
    category: EligibilityCategory
    annual_income: float = Field(..., ge=0)
    state: str
    occupation: str
    education: Optional[str] = None
    marital_status: Optional[str] = None
    disability: bool = False
    bpl_card: bool = False
    rural_area: bool = False
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    def to_filter_dict(self) -> Dict[str, Any]:
        """
        Convert profile to filter dictionary for vector search

        Returns:
            Dictionary of filters for eligibility matching
        """
        return {
            'age': self.age,
            'gender': self.gender.value,
            'category': self.category.value,
            'income': self.annual_income,
            'state': self.state,
            'occupation': self.occupation,
        }
