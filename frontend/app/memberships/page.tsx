import Link from "next/link";

const tiers = [
  {
    name: "Founders",
    price: "$15,000",
    description: "The foundation of our community. Essential access with distinguished benefits.",
    features: [
      "Access to boutique showroom",
      "10% member discount on products",
      "Priority booking for grooming",
      "Quarterly member events",
      "Complimentary consultations",
    ],
    cta: "Apply for Founders",
  },
  {
    name: "Signature",
    price: "$20,000",
    description: "Elevated experience with expanded privileges and personalized service.",
    features: [
      "All Founders benefits",
      "15% member discount",
      "Bespoke tailoring consultations",
      "Exclusive trunk shows",
      "Personal style advisor",
      "Semi-annual member dinners",
    ],
    cta: "Apply for Signature",
  },
  {
    name: "Prestige",
    price: "$35,000",
    description: "Premium tier for the discerning gentleman seeking the finest experience.",
    features: [
      "All Signature benefits",
      "20% member discount",
      "Full bespoke suit allowance",
      "Private event access",
      "Dedicated concierge",
      "Quarterly style sessions",
      "Complimentary grooming package",
    ],
    cta: "Apply for Prestige",
  },
  {
    name: "Executive",
    price: "$45,000",
    description: "The ultimate membership. Unparalleled access and white-glove service.",
    features: [
      "All Prestige benefits",
      "25% member discount",
      "Unlimited bespoke consultations",
      "Exclusive member-only events",
      "24/7 concierge service",
      "Annual wardrobe refresh",
      "Private dining experiences",
      "Complimentary valet & parking",
    ],
    cta: "Apply for Executive",
  },
];

export default function MembershipsPage() {
  return (
    <main className="min-h-screen pt-20 lg:pt-24">
      <section className="py-16 lg:py-24 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-heading text-4xl lg:text-5xl text-white mb-4">
            Membership Tiers
          </h1>
          <p className="text-cream/80 text-lg max-w-2xl">
            Join an exclusive community of discerning gentlemen. Each tier offers
            curated benefits designed to elevate your lifestyle.
          </p>
        </div>
      </section>

      <section className="py-16 lg:py-24 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className="bg-primary border-2 border-secondary/40 hover:border-secondary/70 transition-colors p-8 lg:p-10 flex flex-col"
              >
                <div className="flex items-baseline justify-between mb-4">
                  <h2 className="font-heading text-2xl lg:text-3xl text-white">
                    {tier.name}
                  </h2>
                  <span className="font-heading text-2xl text-secondary">
                    {tier.price}
                  </span>
                </div>
                <p className="text-cream/80 mb-6">{tier.description}</p>
                <ul className="space-y-3 mb-8 flex-grow">
                  {tier.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-start gap-2 text-cream/90 text-sm"
                    >
                      <span className="text-hunter mt-0.5">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/login"
                  className="block w-full py-3 bg-hunter text-white text-center text-sm font-medium uppercase tracking-wider hover:bg-hunter/90 transition-colors"
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
