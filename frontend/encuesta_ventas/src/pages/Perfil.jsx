import React, { useState, useEffect } from 'react';

const NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// Obtener meses desde Enero hasta el mes actual
const obtenerMesesHastaHoy = () => {
  const mesActualIndex = new Date().getMonth();
  
  return NOMBRES_MESES.slice(0, mesActualIndex + 1).map((mes) => ({
    mes,
    cantidad: 0 
  }));
};

const Perfil = ({ usuario, onLogout }) => {
  // Estado inicial con meses dinámicos
  const [statsMes, setStatsMes] = useState(obtenerMesesHastaHoy);

  // Cargar encuestas desde la BD
  useEffect(() => {
    const cargarEstadisticas = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/encuesta/listar');
        if (response.ok) {
          const encuestas = await response.json();
          const mesActualIndex = new Date().getMonth();

          // Estructura de meses hasta el mes actual
          const estructuraMeses = NOMBRES_MESES.slice(0, mesActualIndex + 1).map((mes) => ({
            mes,
            cantidad: 0
          }));

          if (Array.isArray(encuestas)) {
            // Filtro por usuario activo
            const encuestasDelUsuario = encuestas.filter((e) => {
              const idUsuarioActual = usuario?.id || usuario?.id_usuario;
              const nombreUsuarioActual = usuario?.username || usuario?.user;

              return (
                e.id_usuario === idUsuarioActual ||
                e.usuario === nombreUsuarioActual ||
                e.user === nombreUsuarioActual
              );
            });

            encuestasDelUsuario.forEach((encuesta) => {
              if (encuesta.fecha) {
                const fechaObj = new Date(encuesta.fecha);
                const mesEncuesta = fechaObj.getMonth();

                if (!isNaN(mesEncuesta) && mesEncuesta <= mesActualIndex) {
                  estructuraMeses[mesEncuesta].cantidad += 1;
                }
              }
            });
          }

          setStatsMes(estructuraMeses);
        }
      } catch (error) {
        console.log('Error al conectar con la base de datos');
      }
    };

    if (usuario) {
      cargarEstadisticas();
    }
  }, [usuario]);

  // Altura proporcional de las barras
  const maxCantidad = Math.max(...statsMes.map((d) => d.cantidad), 1);

  return (
    <div className="perfil-container">
      <div className="perfil-card">
        {/* ENCABEZADO */}
        <div className="perfil-header">
          <div className="user-details">
            <h2 className="user-fullname">
              {usuario?.nombre || 'Juan'} {usuario?.apellido || 'Pérez'}
            </h2>
            <span className="user-username">
              @{usuario?.username || usuario?.user || 'jperez'}
            </span>
          </div>

          <button className="btn-logout-perfil" onClick={onLogout}>
            Cerrar Sesión
          </button>
        </div>

        <hr className="perfil-divider" />

        {/* GRÁFICO DINÁMICO */}
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