import React, { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RellenarEncuesta from './pages/RellenarEncuesta';
import Perfil from './pages/Perfil';
import Historial from './pages/Historial';
import Plantilla from './pages/Plantilla';
import GestionUsuarios from './Components/GestionUsuarios';
import './App.css';

function App() {
  const [usuario, setUsuario] = useState(() => {
    const guardado = localStorage.getItem('usuario_tecbolt');
    return guardado ? JSON.parse(guardado) : null;
  });
  
  const [vistaActual, setVistaActual] = useState('dashboard');

  const handleLoginSuccess = (usr) => {
    setUsuario(usr);
    setVistaActual('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('usuario_tecbolt');
    setUsuario(null);
    setVistaActual('dashboard');
  };

  if (!usuario) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const LayoutConVolver = ({ children }) => (
    <div style={{ position: 'relative' }}>
      <button className="btn-volver" onClick={() => setVistaActual('dashboard')}>
        ← Volver al Menú
      </button>
      {children}
    </div>
  );

  switch (vistaActual) {
    case 'rellenar':
      return (
        <LayoutConVolver>
          <RellenarEncuesta onGuardadoExitoso={() => setVistaActual('historial')} />
        </LayoutConVolver>
      );
    case 'perfil':
      return (
        <LayoutConVolver>
          <Perfil usuario={usuario} onLogout={handleLogout} onIrAGestion={() => setVistaActual('gestion-usuarios')} />
        </LayoutConVolver>
      );
    case 'gestion-usuarios':
      return (
        <LayoutConVolver>
          <GestionUsuarios onVolver={() => setVistaActual('perfil')} />
        </LayoutConVolver>
      );
    case 'plantilla':
      return <LayoutConVolver><Plantilla /></LayoutConVolver>;
    case 'historial':
      return (
        <LayoutConVolver>
          <Historial usuario={usuario} />
        </LayoutConVolver>
      );
    default:
      return <Dashboard onSelectOption={setVistaActual} onLogout={handleLogout} />;
  }
}

export default App;