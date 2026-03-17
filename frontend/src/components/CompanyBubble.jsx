import React from 'react';

const palettes = [
  'linear-gradient(135deg, #6da5ff, #8f5eff)',
  'linear-gradient(135deg, #6de2ff, #5cd5b8)',
  'linear-gradient(135deg, #ff7ad8, #ff6680)',
  'linear-gradient(135deg, #ffca6a, #ff8f42)',
  'linear-gradient(135deg, #a9ff8b, #59d7a8)'
];

export default function CompanyBubble({ company, onClick, index }) {
  const background = palettes[index % palettes.length];

  return (
    <button className="workspace-tile" onClick={() => onClick(company)}>
      <span className="tile-avatar" style={{ background }}>
        {company.name.slice(0, 2).toUpperCase()}
      </span>
      <strong>{company.name}</strong>
    </button>
  );
}
