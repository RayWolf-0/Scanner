import React from 'react';
import styles from './Dashboard.module.css';

const Dashboard = ({ onSelectOption, onLogout }) => {
  return (
    <div className={styles.dashboardPage}>
      <div className={styles.dashboardContent}>
        <h1 className={styles.dashboardTitle}>Encuestas Tecbolt</h1>
        
        <nav className={styles.dashboardMenu}>
          <button className={styles.menuBtn} onClick={() => onSelectOption('perfil')}>
            Perfil
          </button>
          
          <button className={`${styles.menuBtn} ${styles.highlight}`} onClick={() => onSelectOption('rellenar')}>
            Rellenar Encuesta
          </button>
          
          <button className={styles.menuBtn} onClick={() => onSelectOption('historial')}>
            Historial de Encuestas
          </button>
          
          <button className={`${styles.menuBtn} ${styles.logout}`} onClick={onLogout}>
            Cerrar Sesión
          </button>
        </nav>
      </div>
    </div>
  );
};

export default Dashboard;