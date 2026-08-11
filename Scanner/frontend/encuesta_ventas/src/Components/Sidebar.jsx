import React from "react";

const Sidebar = ({ onLogout }) => {
  return (
    <aside className="sidebar">
      <h3 className="logo">Scanner Tecbolt</h3>
      <a href="#perfil">Perfil</a>
      <a href="#scanner">Scanner (próximamente)</a>
      <a href="#rellenar">Rellenar Encuesta</a>
      <a href="#historial">Historial</a>
      <a href="#plantilla">Plantilla</a>
      
      <button onClick={onLogout || (() => {})} className="btn-logout">
        Cerrar Sesión
      </button>
    </aside>
  );
};

export default Sidebar;