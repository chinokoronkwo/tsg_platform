"""Tests for LMS API endpoints (courses, enrollments, quizzes)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lms import Course, Module, Lesson, Quiz, QuizQuestion, CourseStatus, LessonType, QuestionType


@pytest.mark.asyncio
async def test_list_courses(client: AsyncClient):
    """GET /api/v1/courses/ returns list."""
    response = await client.get("/api/v1/courses/")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_create_course(client: AsyncClient, staff_headers):
    """POST /api/v1/courses/ as staff creates course."""
    data = {
        "title": "Test Course",
        "description": "A test course",
        "status": "draft",
    }
    response = await client.post("/api/v1/courses/", json=data, headers=staff_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test Course"
    assert "id" in body


@pytest.mark.asyncio
async def test_enroll(client: AsyncClient, auth_headers, staff_headers):
    """POST /api/v1/enrollments/ enrolls user in course."""
    # Create course first (staff)
    course_resp = await client.post(
        "/api/v1/courses/",
        json={"title": "Enroll Test Course", "status": "published"},
        headers=staff_headers,
    )
    course_id = course_resp.json()["id"]

    response = await client.post(
        "/api/v1/enrollments/",
        json={"course_id": course_id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["course_id"] == course_id
    assert "id" in body


@pytest.mark.asyncio
async def test_submit_quiz(client: AsyncClient, auth_headers, db_session: AsyncSession):
    """POST /api/v1/quizzes/{id}/submit returns score."""
    # Create course, module, lesson, quiz with question via DB
    course = Course(title="Quiz Course", slug="quiz-course", status=CourseStatus.PUBLISHED)
    db_session.add(course)
    await db_session.flush()

    module = Module(course_id=course.id, title="Module 1", sort_order=0)
    db_session.add(module)
    await db_session.flush()

    lesson = Lesson(module_id=module.id, title="Lesson 1", slug="lesson-1", lesson_type=LessonType.TEXT)
    db_session.add(lesson)
    await db_session.flush()

    quiz = Quiz(lesson_id=lesson.id, title="Quiz 1", passing_score=70)
    db_session.add(quiz)
    await db_session.flush()

    question = QuizQuestion(
        quiz_id=quiz.id,
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="What is 2+2?",
        correct_answer="4",
        points=1,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    response = await client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): "4"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "score" in body
    assert "max_score" in body
    assert "passed" in body
    assert body["passed"] is True
