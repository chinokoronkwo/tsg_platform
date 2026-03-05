"use client";

type CourseStatus = "Draft" | "Published" | "Archived";

interface Course {
  id: string;
  title: string;
  status: CourseStatus;
  instructor: string;
  moduleCount: number;
  enrollmentCount: number;
}

const mockCourses: Course[] = [
  { id: "1", title: "Introduction to Wine", status: "Published", instructor: "Maria Santos", moduleCount: 8, enrollmentCount: 124 },
  { id: "2", title: "Advanced Sommelier", status: "Published", instructor: "James Chen", moduleCount: 12, enrollmentCount: 45 },
  { id: "3", title: "Wine & Food Pairing", status: "Draft", instructor: "Maria Santos", moduleCount: 6, enrollmentCount: 0 },
];

export default function CoursesPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Course Builder</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Create Course
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockCourses.map((course) => (
          <div
            key={course.id}
            className="bg-surface rounded-lg border border-cream/10 p-6 hover:border-cream/20 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <h2 className="font-heading text-lg text-white">{course.title}</h2>
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${
                  course.status === "Published"
                    ? "bg-hunter/30 text-hunter"
                    : course.status === "Draft"
                    ? "bg-cream/20 text-cream/80"
                    : "bg-cream/10 text-cream/50"
                }`}
              >
                {course.status}
              </span>
            </div>
            <p className="text-sm text-cream/60 mb-2">Instructor: {course.instructor}</p>
            <div className="flex gap-4 text-sm text-cream/50">
              <span>{course.moduleCount} modules</span>
              <span>{course.enrollmentCount} enrolled</span>
            </div>
            <div className="mt-4 flex gap-2">
              <button className="text-sm text-secondary hover:text-secondary/80">Edit</button>
              <button className="text-sm text-cream/60 hover:text-cream">View</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
