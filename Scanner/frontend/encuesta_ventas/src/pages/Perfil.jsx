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

// Función auxiliar para obtener el nombre del vendedor
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

  // Efecto para Cargar todas las encuestas
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

  // Efecto para Calcular las estadísticas del gráfico según el filtro
  useEffect(() => {
    const mesActualIndex = new Date().getMonth();
    const estructuraMeses = NOMBRES_MESES.slice(0, mesActualIndex + 1).map((mes) => ({
      mes,
      cantidad: 0
    }));

    if (encuestasGlobales.length > 0) {
      // Filtrar según el rol y la selección
      const encuestasFiltradas = encuestasGlobales.filter((e) => {
        if (esSupervisor) {
          if (vendedorFiltro === 'todos') return true;
          return String(getVendedorNombre(e)) === String(vendedorFiltro);
        } else {
          // El usuario común (vendedor) solo verá sus estadisticas
          if (!idUsuarioActual) return true;
          return Number(e.id_usuario) === Number(idUsuarioActual);
        }
      });

      // Llenar datos del mes
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

  // Obtener lista de vendedores únicos
  const vendedoresUnicos = Array.from(new Set(encuestasGlobales.map(getVendedorNombre))).filter(Boolean);

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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 className="chart-title" style={{ margin: 0 }}>
              Encuestas Realizadas {esSupervisor && vendedorFiltro !== 'todos' ? `por ${vendedorFiltro}` : 'por Mes'}
            </h3>
            
            {/* Filtro para Supervisores */}
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