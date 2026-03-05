"use client";

import { useState } from "react";

interface MediaItem {
  id: string;
  name: string;
  type: "image" | "video" | "document";
  size: string;
  folder: string;
}

const mockMedia: MediaItem[] = [
  { id: "1", name: "wine-tasting-hero.jpg", type: "image", size: "245 KB", folder: "Events" },
  { id: "2", name: "membership-card.png", type: "image", size: "89 KB", folder: "Marketing" },
  { id: "3", name: "course-preview.mp4", type: "video", size: "12 MB", folder: "Courses" },
  { id: "4", name: "logo-dark.svg", type: "image", size: "4 KB", folder: "Branding" },
  { id: "5", name: "menu-spring.pdf", type: "document", size: "1.2 MB", folder: "Events" },
  { id: "6", name: "venue-photo.jpg", type: "image", size: "512 KB", folder: "Events" },
];

const folders = ["All", "Events", "Marketing", "Courses", "Branding"];

export default function MediaPage() {
  const [folder, setFolder] = useState("All");
  const [search, setSearch] = useState("");

  const filtered = mockMedia.filter((m) => {
    if (folder !== "All" && m.folder !== folder) return false;
    if (search && !m.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Media Library</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Upload
        </button>
      </div>

      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 bg-surface border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
          />
        </div>
        <div className="flex gap-2">
          {folders.map((f) => (
            <button
              key={f}
              onClick={() => setFolder(f)}
              className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                folder === f
                  ? "bg-secondary text-primary font-medium"
                  : "bg-surface border border-cream/10 text-cream/80 hover:bg-cream/5"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="border-2 border-dashed border-cream/20 rounded-lg p-12 mb-8 text-center hover:border-secondary/50 transition-colors cursor-pointer">
        <p className="text-cream/60 mb-2">Drag and drop files here, or click to upload</p>
        <p className="text-xs text-cream/40">Images, videos, PDFs up to 50MB</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="bg-surface rounded-lg border border-cream/10 overflow-hidden hover:border-cream/20 transition-colors group"
          >
            <div className="aspect-square bg-surface-2 flex items-center justify-center text-cream/30 text-4xl">
              {item.type === "image" ? "🖼" : item.type === "video" ? "🎬" : "📄"}
            </div>
            <div className="p-3">
              <p className="text-sm text-cream truncate" title={item.name}>{item.name}</p>
              <p className="text-xs text-cream/50">{item.size}</p>
            </div>
            <div className="px-3 pb-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="text-xs text-secondary hover:text-secondary/80">Edit</button>
              <button className="text-xs text-cream/60 hover:text-red-400">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
