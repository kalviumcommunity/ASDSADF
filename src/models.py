# from pydantic import BaseModel, Field
# from typing import Dict, Any, List, Optional
# from enum import Enum

# class PromptType(str, Enum):
#     """Supported prompt types for ASDSADF."""
#     ZERO_SHOT = "zero_shot"
#     ONE_SHOT = "one_shot"
#     MULTI_SHOT = "multi_shot"
#     DYNAMIC = "dynamic"
#     CHAIN_OF_THOUGHT = "chain_of_thought"

# class DifficultyLevel(str, Enum):
#     """Difficulty levels for learning content."""
#     BEGINNER = "beginner"
#     INTERMEDIATE = "intermediate"
#     ADVANCED = "advanced"

# class DocumentType(str, Enum):
#     """Types of documents in the knowledge base."""
#     DOCUMENTATION = "documentation"
#     BLOG = "blog"
#     PROJECT = "project"
#     TUTORIAL = "tutorial"
#     REFERENCE = "reference"

# class UserQuery(BaseModel):
#     """User query model for ASDSADF requests."""
#     message: str = Field(..., description="The user's message or question")
#     session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
#     prompt_type: PromptType = Field(PromptType.ZERO_SHOT, description="Type of prompting to use")
#     context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
#     user_profile: Optional[Dict[str, Any]] = Field(None, description="User's profile information")

# class KnowledgeDocument(BaseModel):
#     """Document model for the knowledge base."""
#     id: str = Field(..., description="Unique identifier for the document")
#     title: str = Field(..., description="Document title")
#     content: str = Field(..., description="Document content")
#     source: str = Field(..., description="Source of the document")
#     document_type: DocumentType = Field(..., description="Type of document")
#     metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# class LearningObjective(BaseModel):
#     """Learning objective model."""
#     objective: str = Field(..., description="The learning objective description")
#     concepts: List[str] = Field(default_factory=list, description="Key concepts to learn")
#     estimated_time: str = Field(..., description="Estimated time to complete")

# class Resource(BaseModel):
#     """Learning resource model."""
#     type: str = Field(..., description="Type of resource (documentation, tutorial, video, etc.)")
#     title: str = Field(..., description="Resource title")
#     url: str = Field(..., description="Resource URL")
#     difficulty: DifficultyLevel = Field(..., description="Difficulty level")
#     estimated_time: str = Field(..., description="Estimated time to complete")
#     description: Optional[str] = Field(None, description="Resource description")

# class Project(BaseModel):
#     """Hands-on project model."""
#     title: str = Field(..., description="Project title")
#     description: str = Field(..., description="Project description")
#     skills_practiced: List[str] = Field(..., description="Skills that will be practiced")
#     deliverables: List[str] = Field(..., description="Expected project deliverables")
#     estimated_time: str = Field(..., description="Estimated time to complete")
#     difficulty: DifficultyLevel = Field(..., description="Project difficulty level")

# class Module(BaseModel):
#     """Learning module model."""
#     module_id: int = Field(..., description="Module identifier")
#     title: str = Field(..., description="Module title")
#     description: str = Field(..., description="Module description")
#     learning_objectives: List[LearningObjective] = Field(..., description="Learning objectives")
#     resources: List[Resource] = Field(..., description="Learning resources")
#     hands_on_project: Project = Field(..., description="Hands-on project")
#     prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
#     success_metrics: List[str] = Field(..., description="How to measure success")

# class Phase(BaseModel):
#     """Learning phase model."""
#     phase_id: int = Field(..., description="Phase identifier")
#     title: str = Field(..., description="Phase title")
#     description: str = Field(..., description="Phase description")
#     duration: str = Field(..., description="Expected duration")
#     modules: List[Module] = Field(..., description="Modules in this phase")
#     phase_objectives: List[str] = Field(..., description="Overall phase objectives")

# class UserProfile(BaseModel):
#     """User profile model."""
#     current_level: DifficultyLevel = Field(..., description="Current skill level")
#     primary_goal: str = Field(..., description="Primary learning goal")
#     timeline: str = Field(..., description="Target timeline")
#     learning_style: Optional[str] = Field(None, description="Preferred learning style")
#     time_commitment: Optional[str] = Field(None, description="Available time per week")
#     experience: Optional[Dict[str, Any]] = Field(None, description="Current experience and skills")
#     interests: Optional[List[str]] = Field(None, description="Areas of interest")

# class Roadmap(BaseModel):
#     """Learning roadmap model."""
#     phases: List[Phase] = Field(..., description="Learning phases")
#     total_duration: str = Field(..., description="Total estimated duration")
#     difficulty_progression: List[DifficultyLevel] = Field(..., description="Difficulty progression")
#     key_technologies: List[str] = Field(..., description="Key technologies covered")

# class ASASSDFResponse(BaseModel):
#     """Complete ASDSADF response model."""
#     user_profile: UserProfile = Field(..., description="Analyzed user profile")
#     roadmap: Roadmap = Field(..., description="Personalized learning roadmap")
#     milestones: List[str] = Field(..., description="Key milestones and checkpoints")
#     next_steps: str = Field(..., description="Immediate next steps")
#     session_id: str = Field(..., description="Session identifier")
#     metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# class EvaluationSample(BaseModel):
#     """Evaluation sample model for testing."""
#     id: str = Field(..., description="Sample identifier")
#     user_prompt: str = Field(..., description="User prompt to test")
#     prompt_type: PromptType = Field(..., description="Type of prompt")
#     expected: Dict[str, Any] = Field(..., description="Expected response structure")

# class EvaluationResult(BaseModel):
#     """Evaluation result model."""
#     sample_id: str = Field(..., description="Sample identifier")
#     correctness_score: float = Field(..., description="Correctness score (0-1)")
#     efficiency_score: float = Field(..., description="Efficiency score (0-1)")
#     scalability_score: float = Field(..., description="Scalability score (0-1)")
#     final_score: float = Field(..., description="Final score (0-100)")
#     passed: bool = Field(..., description="Whether the test passed")
#     notes: List[str] = Field(default_factory=list, description="Additional notes")

# class SystemHealth(BaseModel):
#     """System health check model."""
#     status: str = Field(..., description="Overall system status")
#     agent_initialized: bool = Field(..., description="Whether the agent is initialized")
#     rag_system_ready: bool = Field(..., description="Whether RAG system is ready")
#     gemini_api_available: bool = Field(..., description="Whether Gemini API is available")
#     knowledge_base_stats: Dict[str, Any] = Field(..., description="Knowledge base statistics")
#     version: str = Field(..., description="Application version")

# ...existing code...
from pydantic import BaseModel, Field, root_validator
from typing import Dict, Any, List, Optional
from enum import Enum

class PromptType(str, Enum):
    """Supported prompt types for ASDSADF."""
    ZERO_SHOT = "zero_shot"
    ONE_SHOT = "one_shot"
    MULTI_SHOT = "multi_shot"
    DYNAMIC = "dynamic"
    CHAIN_OF_THOUGHT = "chain_of_thought"

class DifficultyLevel(str, Enum):
    """Difficulty levels for learning content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DocumentType(str, Enum):
    """Types of documents in the knowledge base."""
    DOCUMENTATION = "documentation"
    BLOG = "blog"
    PROJECT = "project"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"

class UserQuery(BaseModel):
    """User query model for ASDSADF requests."""
    message: str = Field(..., description="The user's message or question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    prompt_type: PromptType = Field(PromptType.ZERO_SHOT, description="Type of prompting to use")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User's profile information")

    class Config:
        allow_population_by_field_name = True
        fields = {
            'message': {'alias': 'user_input'}
        }

    @root_validator(pre=True)
    def normalize_prompt_type_and_message(cls, values):
        # Accept user_input as alias for message
        if 'user_input' in values and 'message' not in values:
            values['message'] = values.get('user_input')

        # Normalize prompt_type variants: accept zero-shot, zero_shot, ZERO_SHOT, etc.
        pt = values.get('prompt_type')
        if isinstance(pt, str):
            normalized = pt.strip().lower().replace('-', '_')
            # Map normalized string to PromptType enum if possible
            try:
                values['prompt_type'] = PromptType(normalized)
            except Exception:
                # leave as-is; pydantic will validate and raise if invalid
                values['prompt_type'] = normalized
        return values

class KnowledgeDocument(BaseModel):
    """Document model for the knowledge base."""
    id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Source of the document")
    document_type: DocumentType = Field(..., description="Type of document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class LearningObjective(BaseModel):
    """Learning objective model."""
    objective: str = Field(..., description="The learning objective description")
    concepts: List[str] = Field(default_factory=list, description="Key concepts to learn")
    estimated_time: Optional[str] = Field(None, description="Estimated time to complete")

# Implement missing models used across the codebase
class Resource(BaseModel):
    """Learning resource model."""
    type: str = Field(..., description="Type of resource (documentation, tutorial, video, course, etc.)")
    title: str = Field(..., description="Resource title")
    url: Optional[str] = Field(None, description="Resource URL")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Difficulty level")
    estimated_time: Optional[str] = Field(None, description="Estimated time to consume the resource")
    description: Optional[str] = Field(None, description="Short description of the resource")

class Project(BaseModel):
    """Hands-on project model."""
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    skills_practiced: List[str] = Field(default_factory=list, description="Skills practiced")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    estimated_time: Optional[str] = Field(None, description="Estimated completion time")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Project difficulty level")

class Module(BaseModel):
    """Learning module model."""
    module_id: Optional[int] = Field(None, description="Module identifier")
    title: str = Field(..., description="Module title")
    description: Optional[str] = Field(None, description="Module description")
    learning_objectives: List[LearningObjective] = Field(default_factory=list, description="Learning objectives")
    resources: List[Resource] = Field(default_factory=list, description="Resources for the module")
    hands_on_project: Optional[Project] = Field(None, description="Hands-on project for the module")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for the module")
    success_metrics: List[str] = Field(default_factory=list, description="How to measure success")

class Phase(BaseModel):
    """Learning phase model."""
    phase_id: Optional[int] = Field(None, description="Phase identifier")
    title: str = Field(..., description="Phase title")
    description: Optional[str] = Field(None, description="Phase description")
    duration: Optional[str] = Field(None, description="Expected duration")
    modules: List[Module] = Field(default_factory=list, description="Modules in this phase")
    phase_objectives: List[str] = Field(default_factory=list, description="Phase objectives")

class UserProfile(BaseModel):
    """User profile model."""
    current_level: Optional[DifficultyLevel] = Field(None, description="Current skill level")
    primary_goal: Optional[str] = Field(None, description="Primary learning goal")
    timeline: Optional[str] = Field(None, description="Target timeline")
    learning_style: Optional[str] = Field(None, description="Preferred learning style")
    time_commitment: Optional[str] = Field(None, description="Available time per week")
    experience: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current experience and skills")
    interests: Optional[List[str]] = Field(default_factory=list, description="Areas of interest")

class Roadmap(BaseModel):
    """Learning roadmap model."""
    phases: List[Phase] = Field(default_factory=list, description="Learning phases")
    total_duration: Optional[str] = Field(None, description="Total estimated duration")
    difficulty_progression: List[DifficultyLevel] = Field(default_factory=list, description="Difficulty progression")
    key_technologies: List[str] = Field(default_factory=list, description="Key technologies covered")

class ASASSDFResponse(BaseModel):
    """Complete ASDSADF response model."""
    user_profile: Optional[UserProfile] = Field(None, description="Analyzed user profile")
    roadmap: Optional[Roadmap] = Field(None, description="Personalized learning roadmap")
    milestones: List[str] = Field(default_factory=list, description="Key milestones and checkpoints")
    next_steps: Optional[str] = Field(None, description="Immediate next steps")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class EvaluationSample(BaseModel):
    """Evaluation sample model for testing."""
    id: str = Field(..., description="Sample identifier")
    user_prompt: str = Field(..., description="User prompt to test")
    prompt_type: Optional[PromptType] = Field(None, description="Type of prompt")
    expected: Dict[str, Any] = Field(default_factory=dict, description="Expected response structure")

class EvaluationResult(BaseModel):
    """Evaluation result model."""
    sample_id: str = Field(..., description="Sample identifier")
    correctness_score: float = Field(..., description="Correctness score (0-1)")
    efficiency_score: float = Field(..., description="Efficiency score (0-1)")
    scalability_score: float = Field(..., description="Scalability score (0-1)")
    final_score: float = Field(..., description="Final score (0-100)")
    passed: bool = Field(..., description="Whether the test passed")
    notes: List[str] = Field(default_factory=list, description="Additional notes")

class SystemHealth(BaseModel):
    """System health check model."""
    status: str = Field(..., description="Overall system status")
    agent_initialized: bool = Field(..., description="Whether the agent is initialized")
    rag_system_ready: bool = Field(..., description="Whether RAG system is ready")
    gemini_api_available: bool = Field(..., description="Whether Gemini API is available")
    knowledge_base_stats: Dict[str, Any] = Field(default_factory=dict, description="Knowledge base statistics")
    version: Optional[str] = Field(None, description="Application version")
    active_sessions: Optional[int] = Field(0, description="Number of active sessions")

# Add QueryResponse model expected by agent and API
class QueryResponse(BaseModel):
    """Standard response wrapper returned by the agent/api."""
    response: Dict[str, Any] = Field(default_factory=dict, description="Structured response generated by the agent")
    context_used: List[str] = Field(default_factory=list, description="Context snippets used from the KB")
    retrieval_sources: List[str] = Field(default_factory=list, description="Sources used during retrieval")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    session_id: Optional[str] = Field(None, description="Session identifier for the query")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")