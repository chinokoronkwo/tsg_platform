"""Quizzes API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_staff
from ...models.user import User
from ...services.lms_service import QuizService
from ...schemas.lms import (
    QuizCreate,
    QuizResponse,
    QuizAttemptSubmit,
    QuizAttemptResponse,
)

router = APIRouter()


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get quiz by ID with questions."""
    service = QuizService(db)
    quiz = await service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return QuizResponse.model_validate(quiz)


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    data: QuizCreate,
    lesson_id: int = Query(..., description="Lesson ID to attach quiz to"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Create a new quiz (staff only)."""
    service = QuizService(db)
    quiz = await service.create_quiz(lesson_id, data)
    return QuizResponse.model_validate(quiz)


@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    quiz_id: int,
    data: QuizAttemptSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit quiz attempt (returns score, pass/fail)."""
    service = QuizService(db)
    try:
        attempt = await service.submit_attempt(quiz_id, user.id, data)
        return QuizAttemptResponse.model_validate(attempt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{quiz_id}/results", response_model=list[QuizAttemptResponse])
async def get_quiz_results(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user's quiz results/attempts."""
    service = QuizService(db)
    quiz = await service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    attempts = await service.get_user_attempts(quiz_id, user.id)
    return [QuizAttemptResponse.model_validate(a) for a in attempts]
