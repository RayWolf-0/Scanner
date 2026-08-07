import React, { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RellenarEncuesta from './pages/RellenarEncuesta';
import Perfil from './pages/Perfil';
import Historial from './pages/Historial';
import Plantilla from './pages/Plantilla';
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

  // Login
  if (!usuario) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // boton volver
  const LayoutConVolver = ({ children }) => (
    <div style={{ position: 'relative' }}>
      <button className="btn-volver" onClick={() => setVistaActual('dashboard')}>
        ← Volver al Menú
      </button>
      {children}
    </div>
  );

  // navegar entre páginas
  switch (vistaActual) {
    case 'rellenar':
      return <LayoutConVolver><RellenarEncuesta /></LayoutConVolver>;
    case 'perfil':
      return <LayoutConVolver><Perfil usuario={usuario} /></LayoutConVolver>;
    case 'plantilla':
      return <LayoutConVolver><Plantilla /></LayoutConVolver>;
    default:
      return <Dashboard onSelectOption={setVistaActual} onLogout={handleLogout} />;
    case 'historial':
      return(
        <LayoutConVolver>
          <Historial usuario={usuario} />
        </LayoutConVolver>
      );
  }
}

export default App;