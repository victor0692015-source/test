import { Router } from 'express';
import { pool } from '../config/db.js';
import { authRequired } from '../middleware/auth.js';
import { logActivity } from '../services/activityService.js';
import { asyncHandler } from '../middleware/asyncHandler.js';

const router = Router();
router.use(authRequired);

router.get('/', asyncHandler(async (req, res) => {
  const { search = '', status } = req.query;
  const params = [];
  const filters = [];

  if (search) {
    params.push(`%${search}%`);
    filters.push(`(c.name ILIKE $${params.length} OR c.contact_person ILIKE $${params.length})`);
  }

  if (status && status !== 'all') {
    params.push(status);
    filters.push(`c.deal_status = $${params.length}`);
  }

  const whereClause = filters.length ? `WHERE ${filters.join(' AND ')}` : '';

  const query = `
    SELECT c.*
    FROM companies c
    ${whereClause}
    ORDER BY c.updated_at DESC
  `;

  const result = await pool.query(query, params);
  return res.json(result.rows);
}));

router.post('/', asyncHandler(async (req, res) => {
  const { name, contactPerson, email, phone, dealStatus = 'new' } = req.body;

  const result = await pool.query(
    `INSERT INTO companies (name, contact_person, email, phone, deal_status)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING *`,
    [name, contactPerson, email, phone, dealStatus]
  );

  await logActivity({
    userId: req.user.id,
    companyId: result.rows[0].id,
    action: 'company_created',
    details: `Created company ${name}`
  });

  return res.status(201).json(result.rows[0]);
}));

router.get('/:id', asyncHandler(async (req, res) => {
  const companyId = req.params.id;

  const [company, contacts, notes, tasks, activities] = await Promise.all([
    pool.query('SELECT * FROM companies WHERE id = $1', [companyId]),
    pool.query('SELECT * FROM contacts WHERE company_id = $1 ORDER BY created_at DESC', [companyId]),
    pool.query('SELECT * FROM notes WHERE company_id = $1 ORDER BY created_at DESC', [companyId]),
    pool.query('SELECT * FROM tasks WHERE company_id = $1 ORDER BY due_date NULLS LAST, created_at DESC', [companyId]),
    pool.query(
      `SELECT a.*, u.login AS user_login
       FROM activities a
       LEFT JOIN users u ON u.id = a.user_id
       WHERE a.company_id = $1
       ORDER BY a.created_at DESC`,
      [companyId]
    )
  ]);

  if (!company.rows[0]) {
    return res.status(404).json({ message: 'Company not found' });
  }

  return res.json({
    company: company.rows[0],
    contacts: contacts.rows,
    notes: notes.rows,
    tasks: tasks.rows,
    activities: activities.rows
  });
}));

router.put('/:id', asyncHandler(async (req, res) => {
  const companyId = req.params.id;
  const { name, contactPerson, email, phone, dealStatus } = req.body;

  const result = await pool.query(
    `UPDATE companies
     SET name = $1,
         contact_person = $2,
         email = $3,
         phone = $4,
         deal_status = $5,
         updated_at = NOW()
     WHERE id = $6
     RETURNING *`,
    [name, contactPerson, email, phone, dealStatus, companyId]
  );

  if (!result.rows[0]) {
    return res.status(404).json({ message: 'Company not found' });
  }

  await logActivity({
    userId: req.user.id,
    companyId,
    action: 'company_updated',
    details: `Updated profile for ${name}`
  });

  return res.json(result.rows[0]);
}));

router.patch('/:id/status', asyncHandler(async (req, res) => {
  const { status } = req.body;
  const result = await pool.query(
    `UPDATE companies
     SET deal_status = $1,
         updated_at = NOW()
     WHERE id = $2
     RETURNING *`,
    [status, req.params.id]
  );

  if (!result.rows[0]) {
    return res.status(404).json({ message: 'Company not found' });
  }

  await logActivity({
    userId: req.user.id,
    companyId: req.params.id,
    action: 'status_changed',
    details: `Changed status to ${status}`
  });

  return res.json(result.rows[0]);
}));

router.post('/:id/notes', asyncHandler(async (req, res) => {
  const { content } = req.body;
  const result = await pool.query(
    `INSERT INTO notes (company_id, user_id, content)
     VALUES ($1, $2, $3)
     RETURNING *`,
    [req.params.id, req.user.id, content]
  );

  await logActivity({
    userId: req.user.id,
    companyId: req.params.id,
    action: 'note_added',
    details: content.slice(0, 100)
  });

  return res.status(201).json(result.rows[0]);
}));

router.post('/:id/tasks', asyncHandler(async (req, res) => {
  const { title, description, dueDate } = req.body;
  const result = await pool.query(
    `INSERT INTO tasks (company_id, created_by, title, description, due_date)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING *`,
    [req.params.id, req.user.id, title, description, dueDate || null]
  );

  await logActivity({
    userId: req.user.id,
    companyId: req.params.id,
    action: 'task_created',
    details: `Task: ${title}`
  });

  return res.status(201).json(result.rows[0]);
}));

export default router;
