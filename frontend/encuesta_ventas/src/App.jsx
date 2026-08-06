import React, { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RellenarEncuesta from './pages/RellenarEncuesta';
import './App.css';

function App() {
  const [usuario, setUsuario] = useState(null);
  const [vistaActual, setVistaActual] = useState('dashboard');

  const handleLoginSuccess = (usr) => {
    setUsuario(usr);
    setVistaActual('dashboard');
  };

  const handleLogout = () => {
    setUsuario(null);
    setVistaActual('dashboard');
  };

  // 1. Si no hay usuario logueado, muestra la pantalla de LOGIN
  if (!usuario) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // 2. Si el usuario seleccionó "Rellenar Encuesta"
  if (vistaActual === 'rellenar') {
    return (
      <div style={{ position: 'relative' }}>
        <button className="btn-volver" onClick={() => setVistaActual('dashboard')}>
          ← Volver al Menú
        </button>
        <RellenarEncuesta />
      </div>
    );
  }

  // 3. Por defecto tras loguearse: muestra la página de DASHBOARD (Menú)
  return (
    <Dashboard 
      onSelectOption={(opcion) => setVistaActual(opcion)} 
      onLogout={handleLogout} 
    />
  );
}

export default App;