from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..models.lms import CourseStatus, LessonType, QuestionType


# --- Course ---
class CourseCreate(BaseModel):
    title: str = Field(max_length=300)
    slug: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    status: CourseStatus = CourseStatus.DRAFT
    min_membership_tier: str | None = None
    instructor_id: int | None = None
    difficulty_level: str | None = None
    drip_enabled: bool = False


class CourseUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    status: CourseStatus | None = None
    min_membership_tier: str | None = None
    instructor_id: int | None = None
    difficulty_level: str | None = None
    drip_enabled: bool | None = None


class CourseResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    thumbnail_url: str | None
    status: CourseStatus
    min_membership_tier: str | None
    instructor_id: int | None
    difficulty_level: str | None
    drip_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Module ---
class ModuleCreate(BaseModel):
    title: str = Field(max_length=300)
    description: str | None = None
    sort_order: int = 0
    drip_days_offset: int | None = None


class ModuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    sort_order: int | None = None
    drip_days_offset: int | None = None


class ModuleResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None
    sort_order: int
    drip_days_offset: int | None

    model_config = {"from_attributes": True}


# --- Content Block (for Lesson) ---
class ContentBlockCreate(BaseModel):
    content_type: str = Field(max_length=20)
    body: str | None = None
    video_url: str | None = None
    video_provider: str | None = None
    video_duration_seconds: int | None = None
    resource_url: str | None = None
    resource_name: str | None = None
    sort_order: int = 0


class ContentBlockResponse(BaseModel):
    id: int
    lesson_id: int
    content_type: str
    body: str | None
    video_url: str | None
    video_provider: str | None
    video_duration_seconds: int | None
    resource_url: str | None
    resource_name: str | None
    sort_order: int

    model_config = {"from_attributes": True}


# --- Lesson ---
class LessonCreateInModule(BaseModel):
    module_id: int
    title: str = Field(max_length=300)
    lesson_type: LessonType = LessonType.TEXT
    duration_minutes: int | None = None
    is_free_preview: bool = False
    content_blocks: list[ContentBlockCreate] = []
    sort_order: int = 0


class LessonCreate(BaseModel):
    title: str = Field(max_length=300)
    lesson_type: LessonType = LessonType.TEXT
    duration_minutes: int | None = None
    is_free_preview: bool = False
    content_blocks: list[ContentBlockCreate] = []
    sort_order: int = 0


class LessonUpdate(BaseModel):
    title: str | None = None
    lesson_type: LessonType | None = None
    duration_minutes: int | None = None
    is_free_preview: bool | None = None
    content_blocks: list[ContentBlockCreate] | None = None
    sort_order: int | None = None


class LessonResponse(BaseModel):
    id: int
    module_id: int
    title: str
    slug: str
    lesson_type: LessonType
    sort_order: int
    duration_minutes: int | None
    is_free_preview: bool
    content: list[ContentBlockResponse] = []

    model_config = {"from_attributes": True}


# --- Quiz ---
class QuizQuestionCreate(BaseModel):
    question_type: QuestionType
    question_text: str
    options: dict[str, Any] | None = None
    correct_answer: str
    points: int = 1
    sort_order: int = 0


class QuizCreate(BaseModel):
    title: str = Field(max_length=300)
    description: str | None = None
    passing_score: int = 70
    max_attempts: int | None = None
    time_limit_minutes: int | None = None
    questions: list[QuizQuestionCreate] = []
    sort_order: int = 0


class QuizQuestionResponse(BaseModel):
    id: int
    quiz_id: int
    question_type: QuestionType
    question_text: str
    options: dict[str, Any] | None
    points: int
    sort_order: int

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: int
    lesson_id: int
    title: str
    description: str | None
    passing_score: int
    max_attempts: int | None
    time_limit_minutes: int | None
    questions: list[QuizQuestionResponse] = []

    model_config = {"from_attributes": True}


class QuizAttemptSubmit(BaseModel):
    answers: dict[str, Any] = Field(description="Mapping of question_id (str) to submitted answer")


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    answers: dict[str, Any] | None
    score: int | None
    max_score: int | None
    passed: bool | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# --- Enrollment ---
class EnrollRequest(BaseModel):
    course_id: int


class CourseInfoBrief(BaseModel):
    id: int
    title: str
    slug: str
    thumbnail_url: str | None

    model_config = {"from_attributes": True}


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    course: CourseInfoBrief | None = None
    progress_pct: int
    enrolled_at: datetime
    completed_at: datetime | None
    status: str

    model_config = {"from_attributes": True}


class CourseProgressUpdate(BaseModel):
    lesson_id: int
    is_completed: bool = False
    time_spent_seconds: int = 0


# --- Cohort ---
class CohortCreate(BaseModel):
    course_id: int
    name: str = Field(max_length=200)
    start_date: datetime
    end_date: datetime | None = None
    max_members: int | None = None


class CohortAddMemberRequest(BaseModel):
    user_id: int


class CohortMemberBrief(BaseModel):
    id: int
    user_id: int
    cohort_id: int

    model_config = {"from_attributes": True}


class CohortResponse(BaseModel):
    id: int
    course_id: int
    name: str
    start_date: datetime
    end_date: datetime | None
    max_members: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CohortDetailResponse(CohortResponse):
    members: list[CohortMemberBrief] = []


# --- Discussion ---
class DiscussionThreadCreate(BaseModel):
    course_id: int
    lesson_id: int | None = None
    title: str = Field(max_length=300)
    body: str


class DiscussionThreadUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    is_pinned: bool | None = None
    is_locked: bool | None = None


class DiscussionThreadResponse(BaseModel):
    id: int
    course_id: int
    lesson_id: int | None
    user_id: int
    title: str
    body: str
    is_pinned: bool
    is_locked: bool
    reply_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiscussionThreadDetailResponse(DiscussionThreadResponse):
    posts: list[DiscussionPostResponse] = []


class DiscussionPostCreate(BaseModel):
    body: str
    parent_id: int | None = None
    is_instructor_reply: bool = False


class DiscussionPostResponse(BaseModel):
    id: int
    thread_id: int
    user_id: int
    body: str
    parent_id: int | None
    is_instructor_reply: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Live Session ---
class LiveSessionCreate(BaseModel):
    course_id: int
    title: str = Field(max_length=300)
    description: str | None = None
    instructor_id: int
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_url: str | None = None
    meeting_provider: str | None = None
    max_attendees: int | None = None


class LiveSessionResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None
    instructor_id: int
    scheduled_at: datetime
    duration_minutes: int
    meeting_url: str | None
    meeting_provider: str | None
    status: str
    max_attendees: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Certificate ---
class CertificateTemplateCreate(BaseModel):
    name: str = Field(max_length=200)
    template_html: str | None = None
    is_default: bool = False


class CertificateTemplateResponse(BaseModel):
    id: int
    name: str
    template_html: str | None
    is_default: bool

    model_config = {"from_attributes": True}


class IssuedCertificateResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    certificate_id: int
    issued_at: datetime
    pdf_url: str | None
    verification_code: str

    model_config = {"from_attributes": True}


# --- Pagination ---
class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
