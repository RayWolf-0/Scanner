import React, { useState, useEffect } from 'react';
import styles from './Perfil.module.css';

const NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const parseFechaLocal = (fechaStr) => {
  if (!fechaStr) return null;
  const partes = String(fechaStr).split('T')[0].split('-');
  if (partes.length === 3) {
    return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
  }
  return new Date(fechaStr);
};

const getVendedorNombre = (e) => {
  if (!e) return 'Desconocido';
  if (e.nombre) return `${e.nombre} ${e.apellido || ''}`.trim();
  if (e.username) return e.username;
  if (e.user) return e.user;
  return e.id_usuario || 'Desconocido';
};

const Perfil = ({ usuario, onLogout, onIrAGestion }) => {
  const [encuestasGlobales, setEncuestasGlobales] = useState([]);
  const [statsMes, setStatsMes] = useState([]);
  const [vendedorFiltro, setVendedorFiltro] = useState('todos');
  
  const [passwordActual, setPasswordActual] = useState('');
  const [passwordNueva, setPasswordNueva] = useState('');
  const [mensajePass, setMensajePass] = useState('');

  const datosUsr = usuario?.usuario || usuario; 
  const idUsuarioActual = datosUsr?.id_usuario || datosUsr?.id || datosUsr?.userId;
  
  const rolVal = datosUsr?.rol !== undefined ? datosUsr.rol : datosUsr?.id_rol;
  const textoRol = String(rolVal || '').toLowerCase();
  const textoUsuario = String(datosUsr?.user || datosUsr?.username || datosUsr?.mail || '').toLowerCase();

  const esSupervisor = 
    Number(rolVal) === 2 || 
    textoRol.includes('super') || 
    textoUsuario.includes('mgonza') || 
    textoUsuario.includes('maria');

  const nombreMostrado = 
    datosUsr?.nombre || 
    (datosUsr?.nombres && datosUsr?.apellidos ? `${datosUsr.nombres} ${datosUsr.apellidos}` : null) || 
    datosUsr?.username || 
    datosUsr?.user || 
    datosUsr?.mail || 
    'Usuario';

  useEffect(() => {
    const cargarEncuestas = async () => {
      try {
        const response = await fetch('/api/encuesta/listar');
        if (response.ok) {
          const data = await response.json();
          setEncuestasGlobales(Array.isArray(data) ? data : (data.encuestas || []));
        }
      } catch (error) {
        console.log('Error al conectar con la base de datos', error);
      }
    };

    if (usuario) {
      cargarEncuestas();
    }
  }, [usuario]);

  useEffect(() => {
    const mesActualIndex = new Date().getMonth();
    const estructuraMeses = NOMBRES_MESES.slice(0, mesActualIndex + 1).map((mes) => ({
      mes,
      cantidad: 0
    }));

    if (encuestasGlobales.length > 0) {
      const encuestasFiltradas = encuestasGlobales.filter((e) => {
        if (esSupervisor) {
          if (vendedorFiltro === 'todos') return true;
          return String(getVendedorNombre(e)) === String(vendedorFiltro);
        } else {
          if (!idUsuarioActual) return true;
          return Number(e.id_usuario) === Number(idUsuarioActual);
        }
      });

      encuestasFiltradas.forEach((encuesta) => {
        if (encuesta.fecha) {
          const fechaObj = parseFechaLocal(encuesta.fecha); 
          if (fechaObj && !isNaN(fechaObj.getTime())) {
            const mesEncuesta = fechaObj.getMonth();
            if (mesEncuesta <= mesActualIndex) {
              estructuraMeses[mesEncuesta].cantidad += 1;
            }
          }
        }
      });
    }

    setStatsMes(estructuraMeses);
  }, [encuestasGlobales, vendedorFiltro, esSupervisor, idUsuarioActual]);

  const handleCambiarPassword = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/auth/cambiar-password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_usuario: idUsuarioActual,
          password_actual: passwordActual,
          password_nueva: passwordNueva
        })
      });

      if (res.ok) {
        setMensajePass('¡Contraseña actualizada exitosamente!');
        setPasswordActual('');
        setPasswordNueva('');
      } else {
        const err = await res.json();
        setMensajePass('Error: ' + (err.detail || 'No se pudo actualizar'));
      }
    } catch (error) {
      console.error(error);
      setMensajePass('Error de conexión con el servidor');
    }
  };

  const vendedoresUnicos = Array.from(new Set(encuestasGlobales.map(getVendedorNombre))).filter(Boolean);
  const maxCantidad = statsMes.length > 0 ? Math.max(...statsMes.map((d) => d.cantidad), 1) : 1;

  return (
    <div className={styles.perfilContainer}>
      <div className={styles.perfilCard}>
        
        <div className={styles.perfilHeader}>
          <div className={styles.userDetails}>
            <h2 className={styles.userFullname}>{nombreMostrado}</h2>
            <span className={styles.userUsername}>
              Rol: {esSupervisor ? 'Supervisor' : 'Vendedor'}
            </span>
          </div>

          <button className={styles.btnLogoutPerfil} onClick={onLogout}>
            Cerrar Sesión
          </button>
        </div>

        <hr className={styles.perfilDivider} />

        {esSupervisor && (
          <div style={{ marginBottom: '20px', padding: '15px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#fff' }}>Panel de Supervisión</h3>
            <p style={{ fontSize: '13px', color: '#aaa', margin: '0 0 12px 0' }}>
              Gestión de cuentas de vendedores y permisos del sistema.
            </p>
            <button className="btn-accion btn-excel" onClick={onIrAGestion}>
              Gestionar Usuarios
            </button>
          </div>
        )}

        <div style={{ marginBottom: '20px', padding: '15px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#fff' }}>Cambiar Mi Contraseña</h3>
          <form onSubmit={handleCambiarPassword} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px', color: '#ccc' }}>Contraseña Actual:</label>
              <input 
                type="password" 
                value={passwordActual} 
                onChange={(e) => setPasswordActual(e.target.value)} 
                required 
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px', color: '#ccc' }}>Contraseña Nueva:</label>
              <input 
                type="password" 
                value={passwordNueva} 
                onChange={(e) => setPasswordNueva(e.target.value)} 
                required 
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
              />
            </div>
            <button type="submit" className="btn-accion btn-excel" style={{ marginTop: '5px', background: '#28a745', borderColor: '#28a745' }}>
              Actualizar Contraseña
            </button>
            {mensajePass && <p style={{ fontSize: '13px', color: mensajePass.includes('Error') ? '#ff6b6b' : '#51cf66', margin: '5px 0 0 0' }}>{mensajePass}</p>}
          </form>
        </div>

        <div className={styles.chartSection}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 className={styles.chartTitle} style={{ margin: 0 }}>
              Encuestas Realizadas {esSupervisor && vendedorFiltro !== 'todos' ? `por ${vendedorFiltro}` : 'por Mes'}
            </h3>
            
            {esSupervisor && (
              <select 
                value={vendedorFiltro} 
                onChange={(e) => setVendedorFiltro(e.target.value)}
                style={{ padding: '6px', borderRadius: '4px', background: '#222', color: '#fff', border: '1px solid #444', fontSize: '13px', cursor: 'pointer' }}
              >
                <option value="todos">Todos los usuarios</option>
                {vendedoresUnicos.map((v, idx) => (
                  <option key={idx} value={v}>{v}</option>
                ))}
              </select>
            )}
          </div>

          <div className={styles.barChartContainer}>
            {statsMes.map((item, index) => {
              const porcentaje = (item.cantidad / maxCantidad) * 100;
              return (
                <div key={index} className={styles.barGroup}>
                  <span className={styles.barValue}>{item.cantidad}</span>
                  <div className={styles.barWrapper}>
                    <div
                      className={styles.barFill}
                      style={{ height: `${porcentaje}%` }}
                    />
                  </div>
                  <span className={styles.barLabel}>{item.mes}</span>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Perfil;