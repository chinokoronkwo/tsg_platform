import Link from "next/link";

interface ProductCardProps {
  slug: string;
  name: string;
  price: string | number;
  category: string;
  imageUrl?: string;
}

export function ProductCard({
  slug,
  name,
  price,
  category,
  imageUrl,
}: ProductCardProps) {
  const formattedPrice =
    typeof price === "number" ? `$${price.toLocaleString()}` : price;

  return (
    <Link
      href={`/shop/${slug}`}
      className="group block bg-surface border border-secondary/20 hover:border-secondary/60 transition-all duration-300 overflow-hidden"
    >
      <div className="aspect-[3/4] bg-primary/50 relative overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-cream/30">
            <svg
              className="w-16 h-16"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
            </svg>
          </div>
        )}
        <span className="absolute top-3 left-3 px-2 py-0.5 bg-hunter text-cream text-xs font-medium uppercase tracking-wider">
          {category}
        </span>
      </div>
      <div className="p-4">
        <h3 className="font-heading text-lg text-white group-hover:text-secondary transition-colors">
          {name}
        </h3>
        <p className="mt-1 text-secondary font-medium">{formattedPrice}</p>
      </div>
    </Link>
  );
}
