import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { request } from '../services/api';
import CompanyBubble from '../components/CompanyBubble';
import QuickViewModal from '../components/QuickViewModal';

const statuses = ['all', 'new', 'negotiation', 'won', 'lost'];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', contactPerson: '', email: '', phone: '', dealStatus: 'new' });

  const loadCompanies = async () => {
    const query = new URLSearchParams({ search, status }).toString();
    const data = await request(`/companies?${query}`);
    setCompanies(data);
  };

  useEffect(() => {
    loadCompanies();
  }, [search, status]);

  const createCompany = async (e) => {
    e.preventDefault();
    await request('/companies', { method: 'POST', body: JSON.stringify(form) });
    setForm({ name: '', contactPerson: '', email: '', phone: '', dealStatus: 'new' });
    setShowCreate(false);
    loadCompanies();
  };

  const shownCompanies = useMemo(() => companies.slice(0, 10), [companies]);

  return (
    <div className="dashboard gradient-page">
      <header className="search-shell">
        <span className="search-icon">⌕</span>
        <input placeholder="Поиск" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button className="gear-btn" title="Настройки" type="button">⚙</button>
      </header>

      <section className="workspace-head">
        <h2>Workspace</h2>
        <p>{companies.length} companies</p>
      </section>

      <section className="workspace-grid">
        {shownCompanies.map((company, i) => (
          <CompanyBubble key={company.id} company={company} index={i} onClick={setSelected} />
        ))}

        <button className="add-tile" onClick={() => setShowCreate((v) => !v)}>
          <span>+</span>
          <small>Add</small>
        </button>
      </section>

      {showCreate && (
        <form className="glass-form" onSubmit={createCompany}>
          <h3>Новая компания</h3>
          <input required placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input required placeholder="Контактное лицо" value={form.contactPerson} onChange={(e) => setForm({ ...form, contactPerson: e.target.value })} />
          <input required placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input required placeholder="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <button className="primary-btn" type="submit">Создать</button>
        </form>
      )}

      <QuickViewModal company={selected} onClose={() => setSelected(null)} onOpen={(id) => navigate(`/company/${id}`)} />
    </div>
  );
}
