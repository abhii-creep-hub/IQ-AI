from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class CandidateRank(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    PENDING = "pending"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionCategory(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"
    SCENARIO = "scenario"
    BEHAVIORAL = "behavioral"
    CODING = "coding"


class ResumeStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"
