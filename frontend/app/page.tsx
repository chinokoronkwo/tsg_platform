import Link from "next/link";
import { ProductCard } from "@/components/product-card";

const features = [
  {
    title: "Sartorial",
    subtitle: "Suits & Tailoring",
    description:
      "Bespoke and made-to-measure suits crafted by master tailors. Elevate your wardrobe with timeless elegance.",
    icon: (
      <svg
        className="w-12 h-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    title: "Tonsorial",
    subtitle: "Grooming & Barbering",
    description:
      "Premium grooming services and barber expertise. From classic cuts to modern styles, we refine the gentleman.",
    icon: (
      <svg
        className="w-12 h-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </svg>
    ),
  },
  {
    title: "Cordwainer",
    subtitle: "Shoes & Leather",
    description:
      "Handcrafted footwear and leather goods. Each piece tells a story of craftsmanship and enduring quality.",
    icon: (
      <svg
        className="w-12 h-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 6h16M4 12h16m-7 6h7"
        />
      </svg>
    ),
  },
];

const membershipTiers = [
  { name: "Founders", price: "$15,000", href: "/memberships" },
  { name: "Signature", price: "$20,000", href: "/memberships" },
  { name: "Prestige", price: "$35,000", href: "/memberships" },
  { name: "Executive", price: "$45,000", href: "/memberships" },
];

const featuredProducts = [
  { slug: "bespoke-navy-suit", name: "Bespoke Navy Suit", price: 4500, category: "Suit Snob" },
  { slug: "oxford-derby-shoes", name: "Oxford Derby Shoes", price: 850, category: "Shoe Snob" },
  { slug: "signature-grooming-kit", name: "Signature Grooming Kit", price: 320, category: "Snip Snob" },
  { slug: "cashmere-overcoat", name: "Cashmere Overcoat", price: 2800, category: "Suit Snob" },
];

const testimonials = [
  {
    quote:
      "Snob Group has redefined what luxury means to me. The attention to detail in every service is unparalleled.",
    author: "Alexander W.",
    role: "Founders Member",
  },
  {
    quote:
      "From my first bespoke suit to the grooming services, everything exceeds expectations. Worth every penny.",
    author: "James H.",
    role: "Signature Member",
  },
  {
    quote:
      "The club atmosphere and the caliber of members make this more than a service—it's a lifestyle.",
    author: "Michael R.",
    role: "Executive Member",
  },
];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="min-h-screen flex flex-col justify-center bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary via-primary to-primary/95" />
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `radial-gradient(circle at 2px 2px, rgba(165, 133, 54, 0.3) 1px, transparent 0)`,
              backgroundSize: "32px 32px",
            }}
          />
        </div>
        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center pt-20">
          <h1 className="font-heading text-4xl sm:text-5xl md:text-6xl lg:text-7xl text-white tracking-wide mb-6">
            The Exclusive Boutique Grooming Club
          </h1>
          <p className="text-cream/90 text-lg sm:text-xl max-w-2xl mx-auto mb-10">
            A personalized luxury experience focusing on the sartorial, tonsorial
            and cordwainer needs of our clients.
          </p>
          <Link
            href="/memberships"
            className="inline-block bg-secondary text-white px-10 py-4 text-sm font-bold uppercase tracking-[0.2em] hover:bg-secondary/90 transition-colors"
          >
            Become a Member
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 lg:py-28 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-16">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="text-center group"
              >
                <div className="inline-flex items-center justify-center w-20 h-20 text-secondary mb-6 border border-secondary/40 group-hover:border-secondary transition-colors">
                  {feature.icon}
                </div>
                <h2 className="font-heading text-2xl lg:text-3xl text-white mb-2">
                  {feature.title}
                </h2>
                <p className="text-secondary text-sm uppercase tracking-wider mb-4">
                  {feature.subtitle}
                </p>
                <p className="text-cream/80 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Membership tiers */}
      <section className="py-20 lg:py-28 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-3xl lg:text-4xl text-white text-center mb-4">
            Membership Tiers
          </h2>
          <p className="text-cream/80 text-center max-w-2xl mx-auto mb-16">
            Join an exclusive community of discerning gentlemen. Choose the tier
            that matches your lifestyle.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {membershipTiers.map((tier) => (
              <Link
                key={tier.name}
                href={tier.href}
                className="block p-6 bg-surface border border-secondary/30 hover:border-secondary transition-all duration-300 group"
              >
                <h3 className="font-heading text-xl text-white group-hover:text-secondary transition-colors">
                  {tier.name}
                </h3>
                <p className="mt-2 text-secondary text-2xl font-heading">
                  {tier.price}
                </p>
                <span className="inline-block mt-4 text-cream/80 text-sm uppercase tracking-wider group-hover:text-secondary transition-colors">
                  Learn more →
                </span>
              </Link>
            ))}
          </div>
          <div className="text-center mt-12">
            <Link
              href="/memberships"
              className="inline-block border border-secondary text-secondary px-8 py-3 text-sm font-medium uppercase tracking-wider hover:bg-secondary hover:text-white transition-colors"
            >
              View All Tiers
            </Link>
          </div>
        </div>
      </section>

      {/* Featured products */}
      <section className="py-20 lg:py-28 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-3xl lg:text-4xl text-white mb-4">
            Featured Products
          </h2>
          <p className="text-cream/80 mb-12 max-w-2xl">
            Curated selections from our sartorial, tonsorial, and cordwainer
            collections.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((product) => (
              <ProductCard
                key={product.slug}
                slug={product.slug}
                name={product.name}
                price={product.price}
                category={product.category}
              />
            ))}
          </div>
          <div className="mt-12">
            <Link
              href="/shop"
              className="inline-block border border-secondary text-secondary px-8 py-3 text-sm font-medium uppercase tracking-wider hover:bg-secondary hover:text-white transition-colors"
            >
              Shop All
            </Link>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 lg:py-28 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-3xl lg:text-4xl text-white text-center mb-16">
            What Our Members Say
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <blockquote
                key={testimonial.author}
                className="p-6 bg-surface border-l-4 border-secondary"
              >
                <p className="text-cream/90 italic mb-4">
                  &ldquo;{testimonial.quote}&rdquo;
                </p>
                <footer>
                  <cite className="font-heading text-secondary not-italic">
                    {testimonial.author}
                  </cite>
                  <p className="text-cream/60 text-sm">{testimonial.role}</p>
                </footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
