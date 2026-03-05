"use client";

import { useState } from "react";

interface Event {
  id: string;
  name: string;
  date: string;
  venue: string;
  attendees: number;
}

const mockEvents: Event[] = [
  { id: "1", name: "Wine Tasting Evening", date: "2025-03-15", venue: "Grand Ballroom", attendees: 45 },
  { id: "2", name: "Sommelier Workshop", date: "2025-03-22", venue: "Tasting Room A", attendees: 20 },
  { id: "3", name: "Vintage Release Party", date: "2025-03-28", venue: "Cellar", attendees: 60 },
  { id: "4", name: "Member Mixer", date: "2025-04-05", venue: "Lounge", attendees: 35 },
];

function getDaysInMonth(year: number, month: number) {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const startPad = first.getDay();
  const days = last.getDate();
  return { startPad, days };
}

export default function EventsPage() {
  const [date, setDate] = useState(new Date());
  const year = date.getFullYear();
  const month = date.getMonth();
  const { startPad, days } = getDaysInMonth(year, month);

  const monthEvents = mockEvents.filter((e) => {
    const [y, m] = e.date.split("-").map(Number);
    return y === year && m === month + 1;
  });

  const prevMonth = () => setDate(new Date(year, month - 1));
  const nextMonth = () => setDate(new Date(year, month + 1));

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Event Calendar</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Create Event
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-surface rounded-lg border border-cream/10 overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-cream/10 bg-surface-2">
            <button onClick={prevMonth} className="text-cream/70 hover:text-cream px-2">←</button>
            <h2 className="font-heading text-xl text-white">
              {monthNames[month]} {year}
            </h2>
            <button onClick={nextMonth} className="text-cream/70 hover:text-cream px-2">→</button>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-7 gap-1 text-center text-xs text-cream/50 mb-2">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                <div key={d}>{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: startPad }).map((_, i) => (
                <div key={`pad-${i}`} className="aspect-square" />
              ))}
              {Array.from({ length: days }).map((_, i) => {
                const d = i + 1;
                const dayStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                const hasEvent = monthEvents.some((e) => e.date === dayStr);
                return (
                  <div
                    key={d}
                    className={`aspect-square rounded flex flex-col items-center justify-center text-sm ${
                      hasEvent
                        ? "bg-secondary/20 text-secondary border border-secondary/30"
                        : "bg-surface-2/50 text-cream/80 hover:bg-cream/5"
                    }`}
                  >
                    {d}
                    {hasEvent && <span className="w-1 h-1 rounded-full bg-secondary mt-0.5" />}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <h2 className="font-heading text-lg text-white mb-4">Upcoming Events</h2>
          <div className="space-y-3">
            {mockEvents.slice(0, 4).map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-lg bg-surface-2 border border-cream/10 hover:border-cream/20 transition-colors"
              >
                <p className="text-xs text-secondary uppercase tracking-wider">{ev.date}</p>
                <p className="font-semibold text-white mt-1">{ev.name}</p>
                <p className="text-sm text-cream/60 mt-0.5">{ev.venue}</p>
                <p className="text-sm text-cream/50 mt-1">{ev.attendees} attendees</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
