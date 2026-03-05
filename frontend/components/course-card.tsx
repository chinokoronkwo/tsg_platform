import Link from "next/link";

interface CourseCardProps {
  slug: string;
  title: string;
  instructor: string;
  duration?: string;
  difficulty?: string;
  tierBadge?: string;
  thumbnailUrl?: string;
  progress?: number;
}

export function CourseCard({
  slug,
  title,
  instructor,
  duration,
  difficulty,
  tierBadge,
  thumbnailUrl,
  progress,
}: CourseCardProps) {
  return (
    <Link
      href={`/learn/${slug}`}
      className="group block bg-surface border border-secondary/20 hover:border-secondary/60 transition-all duration-300 overflow-hidden"
    >
      <div className="aspect-video bg-primary/50 relative overflow-hidden">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-cream/30">
            <svg
              className="w-16 h-16"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        )}
        {tierBadge && (
          <span className="absolute top-3 right-3 px-2 py-0.5 bg-secondary/90 text-white text-xs font-medium uppercase tracking-wider">
            {tierBadge}
          </span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-heading text-lg text-white group-hover:text-secondary transition-colors">
          {title}
        </h3>
        <p className="mt-1 text-cream/80 text-sm">{instructor}</p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs text-cream/60">
          {duration && <span>{duration}</span>}
          {difficulty && <span>• {difficulty}</span>}
        </div>
        {progress !== undefined && progress > 0 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-cream/80 mb-1">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-1 bg-primary rounded-full overflow-hidden">
              <div
                className="h-full bg-secondary transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
