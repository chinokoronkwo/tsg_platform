from fastapi import APIRouter

from . import auth, users, products, orders, subscriptions, memberships, wallet
from . import bookings, events, courses, lessons, quizzes, enrollments, cohorts
from . import discussions, media, cms, email, sms, admin

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(products.router, prefix="/products", tags=["Products"])
router.include_router(orders.router, prefix="/orders", tags=["Orders"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
router.include_router(memberships.router, prefix="/memberships", tags=["Memberships"])
router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(courses.router, prefix="/courses", tags=["Courses"])
router.include_router(lessons.router, prefix="/lessons", tags=["Lessons"])
router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
router.include_router(cohorts.router, prefix="/cohorts", tags=["Cohorts"])
router.include_router(discussions.router, prefix="/discussions", tags=["Discussions"])
router.include_router(media.router, prefix="/media", tags=["Media"])
router.include_router(cms.router, prefix="/cms", tags=["CMS"])
router.include_router(email.router, prefix="/email", tags=["Email"])
router.include_router(sms.router, prefix="/sms", tags=["SMS"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
