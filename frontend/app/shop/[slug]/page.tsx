"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

const productData: Record<
  string,
  { name: string; price: number; description: string; category: string }
> = {
  "bespoke-navy-suit": {
    name: "Bespoke Navy Suit",
    price: 4500,
    description:
      "Handcrafted from the finest Italian wool, this bespoke navy suit exemplifies timeless elegance. Each piece is tailored to your exact measurements by our master craftsmen, ensuring a perfect fit and unparalleled comfort. The classic two-button design and peak lapels make it suitable for both business and formal occasions.",
    category: "Suit Snob",
  },
  "charcoal-wool-blazer": {
    name: "Charcoal Wool Blazer",
    price: 2200,
    description:
      "A versatile charcoal wool blazer that transitions seamlessly from office to evening. Features a half-canvas construction and horn buttons. The perfect foundation for any discerning wardrobe.",
    category: "Suit Snob",
  },
  "oxford-derby-shoes": {
    name: "Oxford Derby Shoes",
    price: 850,
    description:
      "Crafted from premium calfskin with a Goodyear-welted construction, these Oxford derby shoes offer durability and sophistication. The classic cap-toe design pairs seamlessly with both suits and smart casual attire. Hand-finished with a mirror shine.",
    category: "Shoe Snob",
  },
  "signature-grooming-kit": {
    name: "Signature Grooming Kit",
    price: 320,
    description:
      "Our curated grooming collection includes premium beard oil, luxury shaving cream, and a handcrafted badger brush. Each product is formulated with natural ingredients to nourish and protect. Presented in an elegant leather case.",
    category: "Snip Snob",
  },
  "cashmere-overcoat": {
    name: "Cashmere Overcoat",
    price: 2800,
    description:
      "Luxurious 100% cashmere overcoat with a timeless single-breasted design. Hand-finished with mother-of-pearl buttons and a fully lined interior. A statement piece for the discerning gentleman.",
    category: "Suit Snob",
  },
  "monk-strap-loafers": {
    name: "Monk Strap Loafers",
    price: 720,
    description:
      "Elegant monk strap loafers in supple calfskin. The double monk design offers a refined alternative to traditional lace-ups. Blake-stitched for flexibility and comfort.",
    category: "Shoe Snob",
  },
  "premium-beard-oil": {
    name: "Premium Beard Oil",
    price: 85,
    description:
      "A nourishing blend of argan and jojoba oils with sandalwood and cedar notes. Promotes healthy beard growth and adds a subtle, sophisticated scent.",
    category: "Snip Snob",
  },
  "tuxedo-dinner-jacket": {
    name: "Tuxedo Dinner Jacket",
    price: 3800,
    description:
      "A peak-lapel dinner jacket in midnight blue Barathea wool. Fully canvased with satin lapels and matching trousers. The epitome of black-tie elegance.",
    category: "Suit Snob",
  },
  "chelsea-boots": {
    name: "Chelsea Boots",
    price: 650,
    description:
      "Classic Chelsea boots in black calfskin with elastic side panels. Goodyear-welted for durability. The perfect boot for both formal and casual occasions.",
    category: "Shoe Snob",
  },
  default: {
    name: "Product",
    price: 0,
    description: "Product description.",
    category: "General",
  },
};

const tabs = ["Description", "Additional Info", "Reviews"];

export default function ProductDetailPage() {
  const params = useParams();
  const slug = (params?.slug as string) || "";
  const product =
    productData[slug] ||
    (slug
      ? {
          ...productData.default,
          name: slug
            .split("-")
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" "),
        }
      : productData.default);
  const [selectedTab, setSelectedTab] = useState("Description");
  const [selectedImage, setSelectedImage] = useState(0);

  const images = [null, null, null];

  return (
    <main className="min-h-screen pt-20 lg:pt-24">
      <section className="py-12 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <nav className="mb-8">
            <Link
              href="/shop"
              className="text-cream/80 text-sm hover:text-secondary transition-colors"
            >
              ← Back to Shop
            </Link>
          </nav>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16">
            {/* Image gallery */}
            <div className="space-y-4">
              <div className="aspect-[3/4] bg-primary/50 flex items-center justify-center">
                <div className="text-cream/30">
                  <svg
                    className="w-24 h-24"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
                  </svg>
                </div>
              </div>
              <div className="flex gap-2">
                {images.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedImage(i)}
                    className={`w-20 h-20 flex-shrink-0 border-2 transition-colors ${
                      selectedImage === i
                        ? "border-secondary"
                        : "border-secondary/20 hover:border-secondary/50"
                    }`}
                  >
                    <div className="w-full h-full bg-primary/50 flex items-center justify-center text-cream/20 text-xs">
                      {i + 1}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Product info */}
            <div>
              <span className="inline-block px-2 py-0.5 bg-hunter text-cream text-xs font-medium uppercase tracking-wider mb-4">
                {product.category}
              </span>
              <h1 className="font-heading text-3xl lg:text-4xl text-white mb-4">
                {product.name}
              </h1>
              <p className="text-2xl text-secondary font-heading mb-8">
                ${product.price.toLocaleString()}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <button className="flex-1 py-3 bg-secondary text-white text-sm font-medium uppercase tracking-wider hover:bg-secondary/90 transition-colors">
                  Add to Cart
                </button>
                <button className="flex-1 py-3 border border-secondary text-secondary text-sm font-medium uppercase tracking-wider hover:bg-secondary hover:text-white transition-colors">
                  Buy Now
                </button>
              </div>

              {/* Tabs */}
              <div className="border-t border-secondary/20 pt-8">
                <div className="flex gap-8 mb-6">
                  {tabs.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setSelectedTab(tab)}
                      className={`text-sm font-medium uppercase tracking-wider transition-colors ${
                        selectedTab === tab
                          ? "text-secondary border-b-2 border-secondary pb-1"
                          : "text-cream/80 hover:text-cream"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="text-cream/90 text-sm leading-relaxed">
                  {selectedTab === "Description" && (
                    <p>{product.description}</p>
                  )}
                  {selectedTab === "Additional Info" && (
                    <div className="space-y-2">
                      <p><strong>Material:</strong> Premium materials</p>
                      <p><strong>Care:</strong> Dry clean only / Follow care label</p>
                      <p><strong>Origin:</strong> Handcrafted</p>
                    </div>
                  )}
                  {selectedTab === "Reviews" && (
                    <p className="text-cream/60">
                      No reviews yet. Be the first to review this product.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
