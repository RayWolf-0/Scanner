import React, { useState, useEffect } from 'react';

const NOMBRES_MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const API_BASE_URL = 'http://localhost:5000/api/encuesta';

const Historial = ({ usuario }) => {
  const [encuestas, setEncuestas] = useState([]);
  const [cargando, setCargando] = useState(true);

  // Filtros de fecha (Por defecto toma el mes y año actual)
  const hoy = new Date();
  const [mesSeleccionado, setMesSeleccionado] = useState(hoy.getMonth());
  const [anioSeleccionado, setAnioSeleccionado] = useState(hoy.getFullYear());

  // Estado para el modal de edición
  const [encuestaEditando, setEncuestaEditando] = useState(null);

  // Helper para convertir cadenas "YYYY-MM-DD" a fecha local sin desfase UTC
  const parseFechaLocal = (fechaStr) => {
    if (!fechaStr) return null;
    const partes = String(fechaStr).split('T')[0].split('-');
    if (partes.length === 3) {
      return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    }
    return new Date(fechaStr);
  };

  // Cargar encuestas desde el backend
  const cargarEncuestas = async () => {
    setCargando(true);
    try {
      const res = await fetch(`${API_BASE_URL}/listar`);
      if (res.ok) {
        const data = await res.json();
        setEncuestas(data);
      } else {
        console.error('Error al obtener encuestas del servidor');
      }
    } catch (error) {
      console.error('Error al cargar encuestas:', error);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarEncuestas();
  }, []);

  // Filtrar encuestas por mes, año y opcionalmente por usuario
  const encuestasFiltradas = encuestas.filter((e) => {
    if (!e.fecha) return false;
    const fechaObj = parseFechaLocal(e.fecha);
    if (!fechaObj || isNaN(fechaObj.getTime())) return false;

    const idUsuarioActual = usuario?.id || usuario?.id_usuario;

    // Coincidencia de mes y año
    const coincideMesAnio =
      fechaObj.getMonth() === Number(mesSeleccionado) &&
      fechaObj.getFullYear() === Number(anioSeleccionado);

    // Si la encuesta tiene ID de usuario, verificar que corresponda
    const coincideUsuario = e.id_usuario ? (Number(e.id_usuario) === Number(idUsuarioActual)) : true;

    return coincideMesAnio && coincideUsuario;
  });

  // Eliminar encuesta
  const handleEliminar = async (id) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta encuesta?')) return;

    try {
      const res = await fetch(`${API_BASE_URL}/eliminar/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setEncuestas(encuestas.filter((item) => (item.id_encuesta || item.id) !== id));
        alert('Encuesta eliminada correctamente');
      } else {
        alert('No se pudo eliminar la encuesta');
      }
    } catch (error) {
      console.error(error);
      alert('Error al conectar con el servidor');
    }
  };

  // Guardar cambios de edición
  const handleGuardarEdicion = async (e) => {
    e.preventDefault();
    const id = encuestaEditando.id_encuesta || encuestaEditando.id;

    try {
      const res = await fetch(`${API_BASE_URL}/actualizar/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(encuestaEditando)
      });

      if (res.ok) {
        setEncuestas(
          encuestas.map((item) =>
            (item.id_encuesta || item.id) === id ? encuestaEditando : item
          )
        );
        setEncuestaEditando(null);
        alert('Encuesta actualizada correctamente');
      } else {
        alert('No se pudo actualizar la encuesta');
      }
    } catch (error) {
      console.error(error);
      alert('Error de conexión al actualizar');
    }
  };

  // descargar archivos excel y pdf
  const descargarArchivo = async (tipo, id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/exportar/${tipo}/${id}`);
      if (!res.ok) throw new Error(`No se pudo generar el archivo ${tipo.toUpperCase()}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Encuesta_Maestra_${id}.${tipo === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      alert(`Error al descargar el ${tipo.toUpperCase()}`);
    }
  };

  return (
    <div className="historial-container">
      <div className="historial-card">
        <h2 className="historial-title">Historial de Encuestas</h2>

        {/* Filtros de mes y año */}
        <div className="filtros-bar">
          <div className="filtro-group">
            <label>Mes:</label>
            <select
              value={mesSeleccionado}
              onChange={(e) => setMesSeleccionado(Number(e.target.value))}
            >
              {NOMBRES_MESES.map((mes, idx) => (
                <option key={idx} value={idx}>{mes}</option>
              ))}
            </select>
          </div>

          <div className="filtro-group">
            <label>Año:</label>
            <select
              value={anioSeleccionado}
              onChange={(e) => setAnioSeleccionado(Number(e.target.value))}
            >
              {[2024, 2025, 2026, 2027].map((anio) => (
                <option key={anio} value={anio}>{anio}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Resultados */}
        {cargando ? (
          <p className="status-msg">Cargando encuestas...</p>
        ) : encuestasFiltradas.length === 0 ? (
          <p className="status-msg">No hay encuestas registradas en {NOMBRES_MESES[mesSeleccionado]} {anioSeleccionado}.</p>
        ) : (
          <div className="tabla-responsive">
            <table className="tabla-historial">
              <thead>
                <tr>
                  <th>Empresa</th>
                  <th>RUT</th>
                  <th>Encuestado</th>
                  <th>Cargo</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {encuestasFiltradas.map((enc) => {
                  const idEnc = enc.id_encuesta || enc.id;
                  return (
                    <tr key={idEnc}>
                      <td>{enc.empresa || 'N/A'}</td>
                      <td>{enc.rut || 'N/A'}</td>
                      <td>{enc.encuestado || 'N/A'}</td>
                      <td>{enc.cargo || 'N/A'}</td>
                      <td>{enc.fecha || 'N/A'}</td>
                      <td className="acciones-td">
                        <button
                          className="btn-accion btn-excel"
                          title="Exportar a Excel"
                          onClick={() => descargarArchivo('excel', idEnc)}
                        >
                          Excel
                        </button>
                        <button
                          className="btn-accion btn-pdf"
                          title="Exportar a PDF"
                          onClick={() => descargarArchivo('pdf', idEnc)}
                        >
                          PDF
                        </button>
                        <button
                          className="btn-accion btn-editar"
                          onClick={() => setEncuestaEditando({ ...enc })}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-accion btn-eliminar"
                          onClick={() => handleEliminar(idEnc)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/*edición de encuesta */}
      {encuestaEditando && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Editar Encuesta</h3>
            <form onSubmit={handleGuardarEdicion}>
              <div className="form-group-modal">
                <label>Nombre Empresa:</label>
                <input
                  type="text"
                  value={encuestaEditando.empresa || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, empresa: e.target.value })}
                  required
                />
              </div>

              <div className="form-group-modal">
                <label>RUT:</label>
                <input
                  type="text"
                  value={encuestaEditando.rut || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, rut: e.target.value })}
                />
              </div>

              <div className="form-group-modal">
                <label>Encuestado(a):</label>
                <input
                  type="text"
                  value={encuestaEditando.encuestado || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, encuestado: e.target.value })}
                  required
                />
              </div>

              <div className="form-group-modal">
                <label>Cargo:</label>
                <input
                  type="text"
                  value={encuestaEditando.cargo || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, cargo: e.target.value })}
                />
              </div>

              <div className="form-group-modal">
                <label>Fecha:</label>
                <input
                  type="date"
                  value={encuestaEditando.fecha || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, fecha: e.target.value })}
                  required
                />
              </div>

              <div className="form-group-modal">
                <label>Teléfono:</label>
                <input
                  type="text"
                  value={encuestaEditando.telefono || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, telefono: e.target.value })}
                />
              </div>

              <div className="form-group-modal">
                <label>Correo Electrónico:</label>
                <input
                  type="email"
                  value={encuestaEditando.correo || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-cancelar" onClick={() => setEncuestaEditando(null)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-guardar-modal">
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Historial;