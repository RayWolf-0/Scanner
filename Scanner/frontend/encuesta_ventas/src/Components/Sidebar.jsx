import React from "react";
import styles from './Sidebar.module.css';

const Sidebar = ({ onLogout }) => {
  return (
    <aside className={styles.sidebar}>
      <h3 className={styles.logo}>Scanner Tecbolt</h3>
      <a href="#perfil" className={styles.menuItem}>Perfil</a>
      <a href="#scanner" className={styles.menuItem}>Scanner (próximamente)</a>
      <a href="#rellenar" className={styles.menuItem}>Rellenar Encuesta</a>
      <a href="#historial" className={styles.menuItem}>Historial</a>
      <a href="#plantilla" className={styles.menuItem}>Plantilla</a>
      
      <button 
        onClick={onLogout || (() => {})} 
        className={`${styles.menuItem} ${styles.logout}`} 
        style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%' }}
      >
        Cerrar Sesión
      </button>
    </aside>
  );
};

export default Sidebar;