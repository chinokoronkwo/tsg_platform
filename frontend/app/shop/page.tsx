"use client";

import { useState } from "react";
import { ProductCard } from "@/components/product-card";

const categories = [
  { id: "all", label: "All Products" },
  { id: "suit", label: "Suit Snob" },
  { id: "shoe", label: "Shoe Snob" },
  { id: "snip", label: "Snip Snob" },
];

const sortOptions = [
  { id: "featured", label: "Featured" },
  { id: "newest", label: "Newest" },
  { id: "price-asc", label: "Price: Low to High" },
  { id: "price-desc", label: "Price: High to Low" },
];

const products = [
  { slug: "bespoke-navy-suit", name: "Bespoke Navy Suit", price: 4500, category: "Suit Snob" },
  { slug: "charcoal-wool-blazer", name: "Charcoal Wool Blazer", price: 2200, category: "Suit Snob" },
  { slug: "oxford-derby-shoes", name: "Oxford Derby Shoes", price: 850, category: "Shoe Snob" },
  { slug: "signature-grooming-kit", name: "Signature Grooming Kit", price: 320, category: "Snip Snob" },
  { slug: "cashmere-overcoat", name: "Cashmere Overcoat", price: 2800, category: "Suit Snob" },
  { slug: "monk-strap-loafers", name: "Monk Strap Loafers", price: 720, category: "Shoe Snob" },
  { slug: "premium-beard-oil", name: "Premium Beard Oil", price: 85, category: "Snip Snob" },
  { slug: "tuxedo-dinner-jacket", name: "Tuxedo Dinner Jacket", price: 3800, category: "Suit Snob" },
  { slug: "chelsea-boots", name: "Chelsea Boots", price: 650, category: "Shoe Snob" },
];

export default function ShopPage() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [sortBy, setSortBy] = useState("featured");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 9;

  const totalPages = Math.ceil(products.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedProducts = products.slice(startIndex, startIndex + itemsPerPage);

  return (
    <main className="min-h-screen pt-20 lg:pt-24">
      <section className="py-12 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-heading text-4xl lg:text-5xl text-white mb-4">
            Shop
          </h1>
          <p className="text-cream/80 text-lg max-w-2xl">
            Curated sartorial, tonsorial, and cordwainer collections for the
            discerning gentleman.
          </p>
        </div>
      </section>

      <section className="py-12 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Sidebar - Category filter */}
            <aside className="lg:w-64 flex-shrink-0">
              <h3 className="font-heading text-lg text-white mb-4 uppercase tracking-wider">
                Categories
              </h3>
              <ul className="space-y-2">
                {categories.map((cat) => (
                  <li key={cat.id}>
                    <button
                      onClick={() => setSelectedCategory(cat.id)}
                      className={`block w-full text-left py-2 px-3 text-sm transition-colors ${
                        selectedCategory === cat.id
                          ? "text-secondary border-l-2 border-secondary pl-2"
                          : "text-cream/80 hover:text-cream"
                      }`}
                    >
                      {cat.label}
                    </button>
                  </li>
                ))}
              </ul>
            </aside>

            {/* Products grid */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                <p className="text-cream/80 text-sm">
                  {products.length} products
                </p>
                <div className="flex items-center gap-2">
                  <label
                    htmlFor="sort"
                    className="text-cream/80 text-sm whitespace-nowrap"
                  >
                    Sort by:
                  </label>
                  <select
                    id="sort"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="bg-primary border border-secondary/30 text-cream px-3 py-2 text-sm focus:outline-none focus:border-secondary"
                  >
                    {sortOptions.map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {paginatedProducts.map((product) => (
                  <ProductCard
                    key={product.slug}
                    slug={product.slug}
                    name={product.name}
                    price={product.price}
                    category={product.category}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-12 flex justify-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 border border-secondary/30 text-cream disabled:opacity-50 disabled:cursor-not-allowed hover:border-secondary transition-colors"
                  >
                    Previous
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (page) => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-4 py-2 ${
                          currentPage === page
                            ? "bg-secondary text-white"
                            : "border border-secondary/30 text-cream hover:border-secondary"
                        } transition-colors`}
                      >
                        {page}
                      </button>
                    )
                  )}
                  <button
                    onClick={() =>
                      setCurrentPage((p) => Math.min(totalPages, p + 1))
                    }
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 border border-secondary/30 text-cream disabled:opacity-50 disabled:cursor-not-allowed hover:border-secondary transition-colors"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
