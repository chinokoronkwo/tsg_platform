"use client";

import { useState } from "react";
import { CourseCard } from "@/components/course-card";

const tierFilters = [
  { id: "all", label: "All Tiers" },
  { id: "founders", label: "Founders" },
  { id: "signature", label: "Signature" },
  { id: "prestige", label: "Prestige" },
  { id: "executive", label: "Executive" },
];

const courses = [
  {
    slug: "art-of-bespoke",
    title: "The Art of Bespoke Tailoring",
    instructor: "Master Tailor James Chen",
    duration: "4 weeks",
    difficulty: "Beginner",
    tierBadge: "Founders+",
  },
  {
    slug: "wardrobe-essentials",
    title: "Building a Capsule Wardrobe",
    instructor: "Style Director Michael Ross",
    duration: "2 weeks",
    difficulty: "Beginner",
    tierBadge: "All Members",
  },
  {
    slug: "shoe-care-masterclass",
    title: "Shoe Care Masterclass",
    instructor: "Cordwainer Expert David Lee",
    duration: "1 week",
    difficulty: "Intermediate",
    tierBadge: "Signature+",
  },
  {
    slug: "grooming-rituals",
    title: "The Gentleman's Grooming Rituals",
    instructor: "Master Barber Alex Thompson",
    duration: "3 weeks",
    difficulty: "Beginner",
    tierBadge: "All Members",
  },
  {
    slug: "fabric-knowledge",
    title: "Understanding Fine Fabrics",
    instructor: "Textile Specialist Sarah Kim",
    duration: "2 weeks",
    difficulty: "Intermediate",
    tierBadge: "Prestige+",
  },
  {
    slug: "evening-wear",
    title: "Mastering Evening Wear",
    instructor: "Style Director Michael Ross",
    duration: "1 week",
    difficulty: "Advanced",
    tierBadge: "Executive",
  },
];

export default function LearnPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTier, setSelectedTier] = useState("all");

  return (
    <main className="min-h-screen pt-20 lg:pt-24">
      <section className="py-12 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-heading text-4xl lg:text-5xl text-white mb-4">
            Learn
          </h1>
          <p className="text-cream/80 text-lg max-w-2xl mb-8">
            Exclusive courses and masterclasses for members. Expand your
            sartorial knowledge with our expert instructors.
          </p>

          {/* Search bar */}
          <div className="max-w-xl">
            <label htmlFor="search" className="sr-only">
              Search courses
            </label>
            <input
              id="search"
              type="search"
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 bg-surface border border-secondary/30 text-cream placeholder-cream/50 focus:outline-none focus:border-secondary transition-colors"
            />
          </div>
        </div>
      </section>

      <section className="py-12 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Filter sidebar */}
            <aside className="lg:w-56 flex-shrink-0">
              <h3 className="font-heading text-lg text-white mb-4 uppercase tracking-wider">
                Membership Access
              </h3>
              <ul className="space-y-2">
                {tierFilters.map((tier) => (
                  <li key={tier.id}>
                    <button
                      onClick={() => setSelectedTier(tier.id)}
                      className={`block w-full text-left py-2 px-3 text-sm transition-colors ${
                        selectedTier === tier.id
                          ? "text-secondary border-l-2 border-secondary pl-2"
                          : "text-cream/80 hover:text-cream"
                      }`}
                    >
                      {tier.label}
                    </button>
                  </li>
                ))}
              </ul>
            </aside>

            {/* Course grid */}
            <div className="flex-1 min-w-0">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {courses.map((course) => (
                  <CourseCard
                    key={course.slug}
                    slug={course.slug}
                    title={course.title}
                    instructor={course.instructor}
                    duration={course.duration}
                    difficulty={course.difficulty}
                    tierBadge={course.tierBadge}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
