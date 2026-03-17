import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { request } from '../services/api';

export default function CompanyPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [note, setNote] = useState('');
  const [task, setTask] = useState({ title: '', description: '', dueDate: '' });

  const loadData = async () => {
    setData(await request(`/companies/${id}`));
  };

  useEffect(() => {
    loadData();
  }, [id]);

  if (!data) return <div className="center-page">Загрузка...</div>;

  const { company, contacts, notes, tasks, activities } = data;

  const updateCompany = async (field, value) => {
    await request(`/companies/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: company.name,
        contactPerson: company.contact_person,
        email: company.email,
        phone: company.phone,
        dealStatus: field === 'dealStatus' ? value : company.deal_status
      })
    });
    if (field !== 'dealStatus') {
      company[field] = value;
    }
    await loadData();
  };

  const addNote = async (e) => {
    e.preventDefault();
    await request(`/companies/${id}/notes`, { method: 'POST', body: JSON.stringify({ content: note }) });
    setNote('');
    loadData();
  };

  const addTask = async (e) => {
    e.preventDefault();
    await request(`/companies/${id}/tasks`, { method: 'POST', body: JSON.stringify(task) });
    setTask({ title: '', description: '', dueDate: '' });
    loadData();
  };

  return (
    <div className="company-page">
      <section className="card">
        <h2>{company.name}</h2>
        <label>Контактное лицо <input value={company.contact_person} onChange={(e) => updateCompany('contact_person', e.target.value)} /></label>
        <label>Email <input value={company.email} onChange={(e) => updateCompany('email', e.target.value)} /></label>
        <label>Телефон <input value={company.phone} onChange={(e) => updateCompany('phone', e.target.value)} /></label>
        <label>Статус
          <select value={company.deal_status} onChange={(e) => request(`/companies/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status: e.target.value }) }).then(loadData)}>
            <option value="new">new</option>
            <option value="negotiation">negotiation</option>
            <option value="won">won</option>
            <option value="lost">lost</option>
          </select>
        </label>
      </section>

      <section className="card">
        <h3>Контакты</h3>
        {contacts.map((c) => <p key={c.id}>{c.name} — {c.email} — {c.phone}</p>)}
      </section>

      <section className="card">
        <h3>Заметки</h3>
        <form onSubmit={addNote}>
          <textarea required value={note} onChange={(e) => setNote(e.target.value)} />
          <button className="primary-btn">Добавить заметку</button>
        </form>
        {notes.map((n) => <p key={n.id}>{n.content}</p>)}
      </section>

      <section className="card">
        <h3>Задачи</h3>
        <form onSubmit={addTask} className="task-form">
          <input required placeholder="Заголовок" value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} />
          <input placeholder="Описание" value={task.description} onChange={(e) => setTask({ ...task, description: e.target.value })} />
          <input type="date" value={task.dueDate} onChange={(e) => setTask({ ...task, dueDate: e.target.value })} />
          <button className="primary-btn">Добавить задачу</button>
        </form>
        {tasks.map((t) => <p key={t.id}>{t.title} ({t.status})</p>)}
      </section>

      <section className="card">
        <h3>История действий</h3>
        {activities.map((a) => (
          <p key={a.id}>{new Date(a.created_at).toLocaleString()} — {a.user_login || 'system'} — {a.action} — {a.details}</p>
        ))}
      </section>
    </div>
  );
}
