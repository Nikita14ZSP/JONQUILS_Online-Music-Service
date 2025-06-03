import React from 'react';
import { Link } from 'react-router-dom';

const RadioPage: React.FC = () => {
  return (
    <div className="container" style={{ padding: '20px', color: '#fff' }}>
      <h1>Радио</h1>
      <p>Здесь будет функционал радио и потоковых станций.</p>
      <p style={{ color: '#ccc' }}>Эта функция будет реализована в будущем.</p>
      
      <Link to="/" style={{ marginTop: '20px', display: 'inline-block' }}>
        На главную
      </Link>
    </div>
  );
};

export default RadioPage;
