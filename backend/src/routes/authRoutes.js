import { Router } from 'express';
import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import { pool } from '../config/db.js';
import { asyncHandler } from '../middleware/asyncHandler.js';

const router = Router();

function verifyPassword(password, passwordHash) {
  if (passwordHash.startsWith('scrypt$')) {
    const [, salt, key] = passwordHash.split('$');
    const derived = crypto.scryptSync(password, salt, 64).toString('hex');
    return crypto.timingSafeEqual(Buffer.from(key, 'hex'), Buffer.from(derived, 'hex'));
  }
  return false;
}

router.post('/login', asyncHandler(async (req, res) => {
  const { login, password } = req.body;
  if (!login || !password) {
    return res.status(400).json({ message: 'Login and password are required' });
  }

  const result = await pool.query('SELECT id, login, password_hash, role FROM users WHERE login = $1', [login]);
  const user = result.rows[0];

  if (!user || !verifyPassword(password, user.password_hash)) {
    return res.status(401).json({ message: 'Invalid credentials' });
  }

  const token = jwt.sign(
    { id: user.id, login: user.login, role: user.role },
    process.env.JWT_SECRET || 'super_secret_key',
    { expiresIn: '12h' }
  );

  return res.json({ token, user: { id: user.id, login: user.login, role: user.role } });
}));

export default router;
