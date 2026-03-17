import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

class MemoryPool {
  constructor() {
    this.ids = { users: 2, companies: 4, contacts: 1, tasks: 1, notes: 1, activities: 1 };
    this.users = [
      {
        id: 1,
        login: 'admin',
        password_hash:
          'scrypt$7cf1bbfbf1703ed134f888f5873570c6$aa2f6bcb319f7508ca45c9b1997c468ab75e07b406d804a21d5ccbae2f0c0553b045ade0473435d9ee35a3464e95d241f273937aeb687a4cd012ebcc318839a4',
        role: 'admin',
        created_at: new Date().toISOString()
      }
    ];
    const now = new Date().toISOString();
    this.companies = [
      { id: 1, name: 'Nord Star Logistics', contact_person: 'Ирина Волкова', email: 'irina@nordstar.io', phone: '+7 901 500 20 10', deal_status: 'negotiation', created_at: now, updated_at: now },
      { id: 2, name: 'Aurum Retail', contact_person: 'Дмитрий Романов', email: 'romanov@aurumretail.ru', phone: '+7 921 001 10 22', deal_status: 'new', created_at: now, updated_at: now },
      { id: 3, name: 'Blue Orbit', contact_person: 'Анна Лебедева', email: 'anna@blueorbit.com', phone: '+7 495 775 40 90', deal_status: 'won', created_at: now, updated_at: now }
    ];
    this.contacts = [];
    this.tasks = [];
    this.notes = [];
    this.activities = [];
  }

  async query(sql, params = []) {
    const text = sql.replace(/\s+/g, ' ').trim();

    if (text.startsWith('SELECT id, login, password_hash, role FROM users WHERE login =')) {
      const login = params[0];
      return { rows: this.users.filter((u) => u.login === login) };
    }

    if (text.startsWith('SELECT c.* FROM companies c')) {
      const hasSearch = text.includes('ILIKE');
      const hasStatus = text.includes('deal_status =');
      let idx = 0;
      let search = null;
      let status = null;
      if (hasSearch) search = String(params[idx++] || '').replace(/%/g, '').toLowerCase();
      if (hasStatus) status = params[idx++];

      let rows = [...this.companies];
      if (search) {
        rows = rows.filter(
          (c) => c.name.toLowerCase().includes(search) || c.contact_person.toLowerCase().includes(search)
        );
      }
      if (status) rows = rows.filter((c) => c.deal_status === status);
      rows.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
      return { rows };
    }

    if (text.startsWith('INSERT INTO companies')) {
      const [name, contactPerson, email, phone, dealStatus] = params;
      const now = new Date().toISOString();
      const row = {
        id: this.ids.companies++,
        name,
        contact_person: contactPerson,
        email,
        phone,
        deal_status: dealStatus,
        created_at: now,
        updated_at: now
      };
      this.companies.push(row);
      return { rows: [row] };
    }

    if (text.startsWith('SELECT * FROM companies WHERE id =')) {
      const id = Number(params[0]);
      return { rows: this.companies.filter((c) => c.id === id) };
    }

    if (text.startsWith('SELECT * FROM contacts WHERE company_id =')) {
      const id = Number(params[0]);
      return { rows: this.contacts.filter((c) => c.company_id === id).sort((a, b) => (a.created_at < b.created_at ? 1 : -1)) };
    }

    if (text.startsWith('SELECT * FROM notes WHERE company_id =')) {
      const id = Number(params[0]);
      return { rows: this.notes.filter((n) => n.company_id === id).sort((a, b) => (a.created_at < b.created_at ? 1 : -1)) };
    }

    if (text.startsWith('SELECT * FROM tasks WHERE company_id =')) {
      const id = Number(params[0]);
      return { rows: this.tasks.filter((t) => t.company_id === id) };
    }

    if (text.startsWith('SELECT a.*, u.login AS user_login FROM activities a')) {
      const id = Number(params[0]);
      const rows = this.activities
        .filter((a) => Number(a.company_id) === id)
        .map((a) => ({ ...a, user_login: this.users.find((u) => u.id === a.user_id)?.login || null }))
        .sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
      return { rows };
    }

    if (text.startsWith('UPDATE companies SET name =')) {
      const [name, contactPerson, email, phone, dealStatus, companyId] = params;
      const id = Number(companyId);
      const row = this.companies.find((c) => c.id === id);
      if (!row) return { rows: [] };
      row.name = name;
      row.contact_person = contactPerson;
      row.email = email;
      row.phone = phone;
      row.deal_status = dealStatus;
      row.updated_at = new Date().toISOString();
      return { rows: [row] };
    }

    if (text.startsWith('UPDATE companies SET deal_status =')) {
      const [status, companyId] = params;
      const row = this.companies.find((c) => c.id === Number(companyId));
      if (!row) return { rows: [] };
      row.deal_status = status;
      row.updated_at = new Date().toISOString();
      return { rows: [row] };
    }

    if (text.startsWith('INSERT INTO notes')) {
      const [companyId, userId, content] = params;
      const row = {
        id: this.ids.notes++,
        company_id: Number(companyId),
        user_id: Number(userId),
        content,
        created_at: new Date().toISOString()
      };
      this.notes.push(row);
      return { rows: [row] };
    }

    if (text.startsWith('INSERT INTO tasks')) {
      const [companyId, createdBy, title, description, dueDate] = params;
      const row = {
        id: this.ids.tasks++,
        company_id: Number(companyId),
        created_by: Number(createdBy),
        title,
        description,
        status: 'open',
        due_date: dueDate || null,
        created_at: new Date().toISOString()
      };
      this.tasks.push(row);
      return { rows: [row] };
    }

    if (text.startsWith('INSERT INTO activities')) {
      const [userId, companyId, action, details] = params;
      const row = {
        id: this.ids.activities++,
        user_id: userId ? Number(userId) : null,
        company_id: companyId ? Number(companyId) : null,
        action,
        details,
        created_at: new Date().toISOString()
      };
      this.activities.push(row);
      return { rows: [row] };
    }

    throw new Error(`MemoryPool query is not implemented for SQL: ${text}`);
  }
}

async function buildPool() {
  const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/watch_crm';
  const pgPool = new Pool({ connectionString });

  try {
    await pgPool.query('SELECT 1');
    console.log('[db] PostgreSQL connected');
    return pgPool;
  } catch (error) {
    console.warn('[db] PostgreSQL недоступен, включён in-memory fallback:', error.code || error.message);
    await pgPool.end().catch(() => {});
    return new MemoryPool();
  }
}

export const pool = await buildPool();
