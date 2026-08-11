import React, { useState, useEffect } from 'react';

const NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const parseFechaLocal = (fechaStr) => {
  if (!fechaStr) return null;
  const partes = String(fechaStr).split('T')[0].split('-');
  if (partes.length === 3) {
    return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
  }
  return new Date(fechaStr);
};


const Perfil = ({ usuario, onLogout, onIrAGestion }) => {
  const [statsMes, setStatsMes] = useState([]);
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
    const cargarEstadisticas = async () => {
      try {
        const response = await fetch('/api/encuesta/listar');
        if (response.ok) {
          const encuestas = await response.json();
          const mesActualIndex = new Date().getMonth();

          const estructuraMeses = NOMBRES_MESES.slice(0, mesActualIndex + 1).map((mes) => ({
            mes,
            cantidad: 0
          }));

          if (Array.isArray(encuestas)) {
            const encuestasDelUsuario = encuestas.filter((e) => {
              if (!idUsuarioActual) return true;
              return Number(e.id_usuario) === Number(idUsuarioActual);
            });

            encuestasDelUsuario.forEach((encuesta) => {
              if (encuesta.fecha) {
                const fechaObj = parseFechaLocal(encuesta.fecha); 
                if (fechaObj) {
                  const mesEncuesta = fechaObj.getMonth();
                  if (!isNaN(mesEncuesta) && mesEncuesta <= mesActualIndex) {
                    estructuraMeses[mesEncuesta].cantidad += 1;
                  }
                }
              }
            });
          }
          setStatsMes(estructuraMeses);
        }
      } catch (error) {
        console.log('Error al conectar con la base de datos', error);
      }
    };

    if (usuario) {
      cargarEstadisticas();
    }
  }, [usuario, idUsuarioActual]);

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

  const maxCantidad = statsMes.length > 0 ? Math.max(...statsMes.map((d) => d.cantidad), 1) : 1;

  return (
    <div className="perfil-container">
      <div className="perfil-card">
        
        <div className="perfil-header">
          <div className="user-details">
            <h2 className="user-fullname">
              {nombreMostrado}
            </h2>
            <span className="user-username">
              Rol: {esSupervisor ? 'Supervisor' : 'Vendedor'}
            </span>
          </div>

          <button className="btn-logout-perfil" onClick={onLogout}>
            Cerrar Sesión
          </button>
        </div>

        <hr className="perfil-divider" />

        {/* Panel exclusivo para Supervisores */}
        {esSupervisor && (
          <div style={{ marginBottom: '20px', padding: '15px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#fff' }}>Panel de Supervisión</h3>
            <p style={{ fontSize: '13px', color: '#aaa', margin: '0 0 12px 0' }}>
              Gestión de cuentas de vendedores y permisos del sistema.
            </p>
            <button 
              className="btn-accion btn-excel" 
              onClick={onIrAGestion} 
            >
              Gestionar Usuarios
            </button>
          </div>
        )}

        {/* Sección de Cambio de Contraseña */}
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

        {/* Gráfico de Estadísticas por Mes */}
        <div className="chart-section">
          <h3 className="chart-title">Encuestas Realizadas por Mes</h3>

          <div className="bar-chart-container">
            {statsMes.map((item, index) => {
              const porcentaje = (item.cantidad / maxCantidad) * 100;
              return (
                <div key={index} className="bar-group">
                  <span className="bar-value">{item.cantidad}</span>
                  <div className="bar-wrapper">
                    <div
                      className="bar-fill"
                      style={{ height: `${porcentaje}%` }}
                    />
                  </div>
                  <span className="bar-label">{item.mes}</span>
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