import { pool } from '../config/db.js';

export async function logActivity({ userId, companyId, action, details }) {
  await pool.query(
    `INSERT INTO activities (user_id, company_id, action, details)
     VALUES ($1, $2, $3, $4)`,
    [userId, companyId, action, details]
  );
}
