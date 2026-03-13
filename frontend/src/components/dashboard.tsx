const columns = ['Todo', 'In Progress', 'Done', 'Overdue'];

export function Dashboard() {
  return (
    <main style={{ fontFamily: 'Inter, sans-serif', padding: 24 }}>
      <h1>CRM Dashboard</h1>
      <section>
        <h2>Client List</h2>
        <p>Search, filter by tags, and open profile timelines.</p>
      </section>
      <section>
        <h2>Task Board (Kanban)</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {columns.map((col) => (
            <article key={col} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12 }}>
              <strong>{col}</strong>
              <p style={{ color: '#666' }}>Tasks appear here.</p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2>Message Inbox</h2>
        <p>Unified inbox for Telegram, WhatsApp, and Viber conversations.</p>
      </section>
      <section>
        <h2>Calendar</h2>
        <p>Upcoming deadlines and reminders.</p>
      </section>
    </main>
  );
}
