import React, { useEffect, useState } from "react";

interface EventItem {
  id: number;
  title: string;
  description: string;
  category: string;
  venue: string;
  start_at: string;
  end_at: string;
  capacity: number;
  status: string;
}

export default function App() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "Workshop",
    venue: "",
    start_at: "2026-11-10T10:00",
    end_at: "2026-11-10T12:00",
    capacity: 50,
  });

  const fetchEvents = async () => {
    try {
      const res = await fetch("/api/v1/events");
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (err) {
      console.error("Failed to fetch events", err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      title: form.title,
      description: form.description,
      category: form.category,
      venue: form.venue,
      start_at: new Date(form.start_at).toISOString(),
      end_at: new Date(form.end_at).toISOString(),
      capacity: form.capacity,
    };

    try {
      if (editingId) {
        await fetch(`/api/v1/events/${editingId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        setEditingId(null);
      } else {
        await fetch("/api/v1/events", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }

      setForm({
        title: "",
        description: "",
        category: "Workshop",
        venue: "",
        start_at: "2026-11-10T10:00",
        end_at: "2026-11-10T12:00",
        capacity: 50,
      });
      fetchEvents();
    } catch (err) {
      console.error("Error submitting form:", err);
    }
  };

  const handleEdit = (ev: EventItem) => {
    setEditingId(ev.id);
    setForm({
      title: ev.title,
      description: ev.description,
      category: ev.category,
      venue: ev.venue,
      start_at: new Date(ev.start_at).toISOString().slice(0, 16),
      end_at: new Date(ev.end_at).toISOString().slice(0, 16),
      capacity: ev.capacity,
    });
  };

  const handleDelete = async (id: number) => {
    await fetch(`/api/v1/events/${id}`, { method: "DELETE" });
    fetchEvents();
  };

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif", maxWidth: 800, margin: "auto" }}>
      <h1>CampusConnect — Event Manager</h1>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 30 }}>
        <h3>{editingId ? "Edit Event" : "Create New Event"}</h3>
        <input
          placeholder="Title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <textarea
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          required
        />
        <input
          placeholder="Category"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
          required
        />
        <input
          placeholder="Venue"
          value={form.venue}
          onChange={(e) => setForm({ ...form, venue: e.target.value })}
          required
        />
        <label>
          Start Time:{" "}
          <input
            type="datetime-local"
            value={form.start_at}
            onChange={(e) => setForm({ ...form, start_at: e.target.value })}
            required
          />
        </label>
        <label>
          End Time:{" "}
          <input
            type="datetime-local"
            value={form.end_at}
            onChange={(e) => setForm({ ...form, end_at: e.target.value })}
            required
          />
        </label>
        <label>
          Capacity:{" "}
          <input
            type="number"
            value={form.capacity}
            onChange={(e) => setForm({ ...form, capacity: parseInt(e.target.value) || 0 })}
            required
          />
        </label>
        <button type="submit">{editingId ? "Update Event" : "Create Event"}</button>
      </form>

      <h2>Events List ({events.length})</h2>
      {events.map((ev) => (
        <div key={ev.id} style={{ border: "1px solid #ccc", padding: 15, borderRadius: 5, marginBottom: 10 }}>
          <h3>
            {ev.title} ({ev.category})
          </h3>
          <p>{ev.description}</p>
          <p>
            📍 <strong>Venue:</strong> {ev.venue} | 👥 <strong>Capacity:</strong> {ev.capacity}
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => handleEdit(ev)}>Edit</button>
            <button onClick={() => handleDelete(ev.id)} style={{ color: "red" }}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}