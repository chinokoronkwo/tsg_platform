import type { Metadata } from "next";
import Link from "next/link";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://thesnobgroup.com";

export const metadata: Metadata = {
  title: "Book an Appointment | Snob Group",
  description:
    "Schedule your grooming, tailoring, or consultation appointment with The Snob Group.",
  openGraph: {
    title: "Book an Appointment | Snob Group",
    description:
      "Schedule your grooming, tailoring, or consultation appointment.",
    url: `${BASE_URL}/book`,
  },
  alternates: { canonical: `${BASE_URL}/book` },
};

export default function BookPage() {
  return (
    <main className="min-h-screen pt-20 lg:pt-24 flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <h1 className="font-heading text-3xl lg:text-4xl text-white mb-4">
          Book Appointment
        </h1>
        <p className="text-cream/80 mb-8">
          Schedule your grooming, tailoring, or consultation appointment. Please
          log in to access the booking system.
        </p>
        <Link
          href="/login"
          className="inline-block bg-secondary text-white px-10 py-4 text-sm font-bold uppercase tracking-[0.2em] hover:bg-secondary/90 transition-colors"
        >
          Log In to Book
        </Link>
      </div>
    </main>
  );
}
