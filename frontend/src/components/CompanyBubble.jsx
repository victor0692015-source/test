import React from 'react';

const palette = ['#5ddcff', '#60ff8b', '#ffa44f', '#7c8bff', '#ff5d7a', '#ffd84f'];

export default function CompanyBubble({ company, onClick, index }) {
  const color = palette[index % palette.length];
  return (
    <button className="bubble" style={{ background: color }} onClick={() => onClick(company)}>
      <span>{company.name.slice(0, 2).toUpperCase()}</span>
    </button>
  );
}
