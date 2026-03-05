import secrets
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from python_slugify import slugify

from ..models.lms import *
from ..schemas.lms import *


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_courses(
        self,
        skip: int = 0,
        limit: int = 20,
        status: CourseStatus | None = None,
        min_membership_tier: str | None = None,
        search: str | None = None,
        instructor_id: int | None = None,
    ) -> tuple[list[Course], int]:
        query = select(Course)

        if status is not None:
            query = query.where(Course.status == status)
        if min_membership_tier:
            query = query.where(Course.min_membership_tier == min_membership_tier)
        if search:
            query = query.where(
                Course.title.ilike(f"%{search}%") | Course.description.ilike(f"%{search}%")
            )
        if instructor_id is not None:
            query = query.where(Course.instructor_id == instructor_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            query.options(
                selectinload(Course.modules).selectinload(Module.lessons),
                selectinload(Course.instructor),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Course.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique().all()), total

    async def get_course(self, course_id: int) -> Course | None:
        result = await self.db.execute(
            select(Course)
            .options(
                selectinload(Course.modules).selectinload(Module.lessons).selectinload(Lesson.content),
                selectinload(Course.instructor),
            )
            .where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def get_course_by_slug(self, slug: str) -> Course | None:
        result = await self.db.execute(
            select(Course)
            .options(
                selectinload(Course.modules).selectinload(Module.lessons),
                selectinload(Course.instructor),
            )
            .where(Course.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_course(self, data: CourseCreate) -> Course:
        slug = data.slug or slugify(data.title)
        existing = await self.db.execute(select(Course).where(Course.slug == slug))
        if existing.scalar_one_or_none():
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        course = Course(
            title=data.title,
            slug=slug,
            description=data.description,
            thumbnail_url=data.thumbnail_url,
            status=data.status,
            min_membership_tier=data.min_membership_tier,
            instructor_id=data.instructor_id,
            difficulty_level=data.difficulty_level,
            drip_enabled=data.drip_enabled,
        )
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def update_course(self, course_id: int, data: CourseUpdate) -> Course | None:
        course = await self.get_course(course_id)
        if not course:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)

        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def delete_course(self, course_id: int) -> bool:
        course = await self.get_course(course_id)
        if not course:
            return False
        await self.db.delete(course)
        await self.db.commit()
        return True


class LessonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lesson(self, lesson_id: int) -> Lesson | None:
        result = await self.db.execute(
            select(Lesson)
            .options(
                selectinload(Lesson.content),
                selectinload(Lesson.quizzes).selectinload(Quiz.questions),
            )
            .where(Lesson.id == lesson_id)
        )
        return result.scalar_one_or_none()

    async def create_lesson(self, module_id: int, data: LessonCreate) -> Lesson:
        slug = slugify(data.title)
        lesson = Lesson(
            module_id=module_id,
            title=data.title,
            slug=slug,
            lesson_type=data.lesson_type,
            duration_minutes=data.duration_minutes,
            is_free_preview=data.is_free_preview,
            sort_order=data.sort_order,
        )
        self.db.add(lesson)
        await self.db.flush()

        for i, block in enumerate(data.content_blocks):
            content = LessonContent(
                lesson_id=lesson.id,
                content_type=block.content_type,
                body=block.body,
                video_url=block.video_url,
                video_provider=block.video_provider,
                video_duration_seconds=block.video_duration_seconds,
                resource_url=block.resource_url,
                resource_name=block.resource_name,
                sort_order=block.sort_order if block.sort_order else i,
            )
            self.db.add(content)

        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def update_lesson(self, lesson_id: int, data: LessonUpdate) -> Lesson | None:
        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return None

        update_data = data.model_dump(exclude_unset=True)
        content_blocks = update_data.pop("content_blocks", None)

        for key, value in update_data.items():
            setattr(lesson, key, value)

        if content_blocks is not None:
            for existing in lesson.content:
                await self.db.delete(existing)
            for i, block in enumerate(content_blocks):
                content = LessonContent(
                    lesson_id=lesson.id,
                    content_type=block.content_type,
                    body=block.body,
                    video_url=block.video_url,
                    video_provider=block.video_provider,
                    video_duration_seconds=block.video_duration_seconds,
                    resource_url=block.resource_url,
                    resource_name=block.resource_name,
                    sort_order=block.sort_order if block.sort_order else i,
                )
                self.db.add(content)

        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def delete_lesson(self, lesson_id: int) -> bool:
        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return False
        await self.db.delete(lesson)
        await self.db.commit()
        return True


class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quiz(self, quiz_id: int) -> Quiz | None:
        result = await self.db.execute(
            select(Quiz)
            .options(
                selectinload(Quiz.questions),
                selectinload(Quiz.lesson),
            )
            .where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()

    async def list_quizzes(
        self,
        lesson_id: int | None = None,
        course_id: int | None = None,
    ) -> list[Quiz]:
        query = select(Quiz).options(selectinload(Quiz.questions))
        if lesson_id is not None:
            query = query.where(Quiz.lesson_id == lesson_id)
        if course_id is not None:
            query = (
                query.join(Lesson)
                .join(Module)
                .where(Module.course_id == course_id)
            )
        query = query.order_by(Quiz.sort_order)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_user_attempts(self, quiz_id: int, user_id: int) -> list[QuizAttempt]:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.completed_at.desc())
        )
        return list(result.scalars().all())

    async def create_quiz(self, lesson_id: int, data: QuizCreate) -> Quiz:
        quiz = Quiz(
            lesson_id=lesson_id,
            title=data.title,
            description=data.description,
            passing_score=data.passing_score,
            max_attempts=data.max_attempts,
            time_limit_minutes=data.time_limit_minutes,
            sort_order=data.sort_order,
        )
        self.db.add(quiz)
        await self.db.flush()

        for i, q in enumerate(data.questions):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                correct_answer=q.correct_answer,
                points=q.points,
                sort_order=q.sort_order if q.sort_order else i,
            )
            self.db.add(question)

        await self.db.commit()
        await self.db.refresh(quiz)
        return quiz

    async def submit_attempt(
        self, quiz_id: int, user_id: int, data: QuizAttemptSubmit
    ) -> QuizAttempt:
        result = await self.db.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == quiz_id)
        )
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise ValueError("Quiz not found")

        earned_points = 0
        max_score = 0

        for question in quiz.questions:
            max_score += question.points
            submitted = data.answers.get(str(question.id))
            if submitted is not None:
                correct = str(submitted).strip().lower() == str(question.correct_answer).strip().lower()
                if correct:
                    earned_points += question.points

        score_pct = int((earned_points / max_score * 100)) if max_score > 0 else 0
        passed = score_pct >= quiz.passing_score

        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            answers=data.answers,
            score=earned_points,
            max_score=max_score,
            passed=passed,
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt


class EnrollmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def enroll_user(self, user_id: int, course_id: int) -> Enrollment:
        existing = await self.db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already enrolled in this course")

        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

    async def get_enrollment(
        self, user_id: int, course_id: int, load_course: bool = False
    ) -> Enrollment | None:
        query = select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
        if load_course:
            query = query.options(selectinload(Enrollment.course))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_enrollment_by_id(
        self, enrollment_id: int, user_id: int | None = None
    ) -> Enrollment | None:
        query = select(Enrollment).options(
            selectinload(Enrollment.course),
            selectinload(Enrollment.progress),
        ).where(Enrollment.id == enrollment_id)
        if user_id is not None:
            query = query.where(Enrollment.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_enrollments(self, user_id: int) -> list[Enrollment]:
        result = await self.db.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.course))
            .where(Enrollment.user_id == user_id)
            .order_by(Enrollment.enrolled_at.desc())
        )
        return list(result.scalars().unique().all())

    def _count_total_lessons(self, course: Course) -> int:
        total = 0
        for module in course.modules:
            total += len(module.lessons)
        return total

    async def update_progress(
        self, user_id: int, course_id: int, data: CourseProgressUpdate
    ) -> Enrollment | None:
        enrollment = await self.get_enrollment(user_id, course_id)
        if not enrollment:
            return None

        result = await self.db.execute(
            select(CourseProgress).where(
                CourseProgress.enrollment_id == enrollment.id,
                CourseProgress.lesson_id == data.lesson_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.is_completed = data.is_completed
            progress.time_spent_seconds = data.time_spent_seconds
            if data.is_completed:
                progress.completed_at = datetime.now(timezone.utc)
        else:
            progress = CourseProgress(
                enrollment_id=enrollment.id,
                lesson_id=data.lesson_id,
                is_completed=data.is_completed,
                time_spent_seconds=data.time_spent_seconds,
                completed_at=datetime.now(timezone.utc) if data.is_completed else None,
            )
            self.db.add(progress)

        await self.db.flush()

        course_result = await self.db.execute(
            select(Course)
            .options(
                selectinload(Course.modules).selectinload(Module.lessons),
            )
            .where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        if not course:
            await self.db.commit()
            await self.db.refresh(enrollment)
            return enrollment

        total_lessons = self._count_total_lessons(course)
        if total_lessons == 0:
            progress_pct = 0
        else:
            completed_result = await self.db.execute(
                select(func.count())
                .select_from(CourseProgress)
                .where(
                    CourseProgress.enrollment_id == enrollment.id,
                    CourseProgress.is_completed == True,
                )
            )
            completed_count = completed_result.scalar() or 0
            progress_pct = int(completed_count / total_lessons * 100)

        enrollment.progress_pct = min(progress_pct, 100)

        if progress_pct >= 100:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.now(timezone.utc)
            if course.certificate_template_id:
                cert_service = CertificateService(self.db)
                await cert_service.generate_certificate(
                    user_id=user_id,
                    course_id=course_id,
                    certificate_id=course.certificate_template_id,
                )

        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment


class CohortService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_cohorts(
        self, course_id: int | None = None
    ) -> list[Cohort]:
        query = select(Cohort).options(selectinload(Cohort.course))
        if course_id is not None:
            query = query.where(Cohort.course_id == course_id)
        query = query.order_by(Cohort.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def create_cohort(self, data: CohortCreate) -> Cohort:
        cohort = Cohort(
            course_id=data.course_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            max_members=data.max_members,
        )
        self.db.add(cohort)
        await self.db.commit()
        await self.db.refresh(cohort)
        return cohort

    async def get_cohort(self, cohort_id: int) -> Cohort | None:
        result = await self.db.execute(
            select(Cohort)
            .options(
                selectinload(Cohort.members),
                selectinload(Cohort.course),
            )
            .where(Cohort.id == cohort_id)
        )
        return result.scalar_one_or_none()

    async def add_member(self, cohort_id: int, user_id: int) -> CohortMember:
        cohort = await self.get_cohort(cohort_id)
        if not cohort:
            raise ValueError("Cohort not found")
        if cohort.max_members is not None:
            member_count = len(cohort.members)
            if member_count >= cohort.max_members:
                raise ValueError("Cohort is full")

        existing = await self.db.execute(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already in cohort")

        member = CohortMember(cohort_id=cohort_id, user_id=user_id)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, cohort_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await self.db.delete(member)
        await self.db.commit()
        return True


class DiscussionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_thread(self, user_id: int, data: DiscussionThreadCreate) -> DiscussionThread:
        thread = DiscussionThread(
            course_id=data.course_id,
            lesson_id=data.lesson_id,
            user_id=user_id,
            title=data.title,
            body=data.body,
        )
        self.db.add(thread)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def get_thread(self, thread_id: int) -> DiscussionThread | None:
        result = await self.db.execute(
            select(DiscussionThread)
            .options(
                selectinload(DiscussionThread.posts),
                selectinload(DiscussionThread.user),
            )
            .where(DiscussionThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def list_threads(
        self, course_id: int, lesson_id: int | None = None
    ) -> list[DiscussionThread]:
        query = (
            select(DiscussionThread)
            .options(selectinload(DiscussionThread.user))
            .where(DiscussionThread.course_id == course_id)
        )
        if lesson_id is not None:
            query = query.where(DiscussionThread.lesson_id == lesson_id)
        query = query.order_by(
            DiscussionThread.is_pinned.desc(),
            DiscussionThread.created_at.desc(),
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def update_thread(
        self, thread_id: int, data: DiscussionThreadUpdate
    ) -> DiscussionThread | None:
        thread = await self.get_thread(thread_id)
        if not thread:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(thread, key, value)

        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def pin_thread(self, thread_id: int, pinned: bool = True) -> DiscussionThread | None:
        return await self.update_thread(thread_id, DiscussionThreadUpdate(is_pinned=pinned))

    async def lock_thread(self, thread_id: int, locked: bool = True) -> DiscussionThread | None:
        return await self.update_thread(thread_id, DiscussionThreadUpdate(is_locked=locked))

    async def create_post(
        self, thread_id: int, user_id: int, data: DiscussionPostCreate
    ) -> DiscussionPost:
        thread = await self.get_thread(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        if thread.is_locked:
            raise ValueError("Thread is locked")

        post = DiscussionPost(
            thread_id=thread_id,
            user_id=user_id,
            body=data.body,
            parent_id=data.parent_id,
            is_instructor_reply=data.is_instructor_reply,
        )
        self.db.add(post)
        thread.reply_count += 1
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_thread(self, thread_id: int) -> bool:
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        await self.db.delete(thread)
        await self.db.commit()
        return True


class CertificateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_verification_code(self) -> str:
        return secrets.token_urlsafe(16)

    async def create_template(self, data: CertificateTemplateCreate) -> Certificate:
        cert = Certificate(
            name=data.name,
            template_html=data.template_html,
            is_default=data.is_default,
        )
        self.db.add(cert)
        await self.db.commit()
        await self.db.refresh(cert)
        return cert

    async def generate_certificate(
        self, user_id: int, course_id: int, certificate_id: int
    ) -> IssuedCertificate:
        verification_code = self._generate_verification_code()

        issued = IssuedCertificate(
            user_id=user_id,
            course_id=course_id,
            certificate_id=certificate_id,
            verification_code=verification_code,
        )
        self.db.add(issued)
        await self.db.commit()
        await self.db.refresh(issued)
        return issued
