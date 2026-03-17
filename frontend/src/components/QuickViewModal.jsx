import React from 'react';

export default function QuickViewModal({ company, onClose, onOpen }) {
  if (!company) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="card" onClick={(e) => e.stopPropagation()}>
        <h3>{company.name}</h3>
        <p><strong>Контакт:</strong> {company.contact_person}</p>
        <p><strong>Email:</strong> {company.email}</p>
        <p><strong>Телефон:</strong> {company.phone}</p>
        <p><strong>Статус:</strong> {company.deal_status}</p>
        <p><strong>Обновлено:</strong> {new Date(company.updated_at).toLocaleString()}</p>
        <button className="primary-btn" onClick={() => onOpen(company.id)}>Открыть компанию</button>
      </div>
    </div>
  );
}
