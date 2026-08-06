import React from 'react';

const Dashboard = ({ onSelectOption, onLogout }) => {
  return (
    <div className="dashboard-page">
      <div className="dashboard-content">
        <h1 className="dashboard-title">Encuestas Tecbolt</h1>
        
        <nav className="dashboard-menu">
          <button className="menu-btn" onClick={() => alert('Sección Perfil')}>
            Perfil
          </button>
          <button className="menu-btn" onClick={() => alert('Sección Scanner')}>
            Scanner (proximamente)
          </button>
          <button className="menu-btn highlight" onClick={() => onSelectOption('rellenar')}>
            Rellenar Encuesta
          </button>
          <button className="menu-btn" onClick={() => alert('Sección Historial')}>
            Historial de Encuestas
          </button>
          <button className="menu-btn" onClick={() => alert('Sección Plantilla')}>
            Plantilla Encuestas
          </button>
          
          <button className="menu-btn logout" onClick={onLogout}>
            Cerrar Sesión
          </button>
        </nav>
      </div>
    </div>
  );
};

export default Dashboard;