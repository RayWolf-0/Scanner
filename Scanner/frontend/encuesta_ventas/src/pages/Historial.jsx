import React, { useState, useEffect } from 'react';
import { pdf } from '@react-pdf/renderer';
import EncuestaPDF from '../Components/EncuestaPDF';

const NOMBRES_MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const REDES_OPCIONES = ['Instagram', 'TikTok', 'Facebook', 'LinkedIn', 'Pinterest', 'Ninguna'];

const API_BASE_URL = '/api/encuesta';

const Historial = ({ usuario }) => {
  const [encuestas, setEncuestas] = useState([]);
  const [cargando, setCargando] = useState(true);

  const usuarioGuardado = JSON.parse(localStorage.getItem('usuario_tecbolt') || '{}');
  const datosUsr = usuario?.usuario || usuario || usuarioGuardado;
  const rolVal = datosUsr?.rol !== undefined ? datosUsr.rol : datosUsr?.id_rol;
  const textoRol = String(rolVal || '').toLowerCase();
  const esSupervisor = Number(rolVal) === 2 || textoRol.includes('super');
  const idUsuarioActual = datosUsr?.id_usuario || datosUsr?.id || datosUsr?.userId || usuarioGuardado.id_usuario || usuarioGuardado.id;

  const hoy = new Date();
  const [mesSeleccionado, setMesSeleccionado] = useState(hoy.getMonth());
  const [anioSeleccionado, setAnioSeleccionado] = useState(hoy.getFullYear());
  const [encuestaEditando, setEncuestaEditando] = useState(null);

  const parseFechaLocal = (fechaStr) => {
    if (!fechaStr) return null;
    const partes = String(fechaStr).split('T')[0].split('-');
    if (partes.length === 3) {
      return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    }
    return new Date(fechaStr);
  };

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

  const encuestasFiltradas = encuestas.filter((e) => {
    if (!e.fecha) return false;
    const fechaObj = parseFechaLocal(e.fecha);
    if (!fechaObj || isNaN(fechaObj.getTime())) return false;

    const coincideMesAnio =
      fechaObj.getMonth() === Number(mesSeleccionado) &&
      fechaObj.getFullYear() === Number(anioSeleccionado);

    // Supervisor ve todo, Vendedor ve únicamente las suyas
    const coincideUsuario = esSupervisor ? true : (idUsuarioActual && e.id_usuario ? Number(e.id_usuario) === Number(idUsuarioActual) : true); 

    return coincideMesAnio && coincideUsuario;
  });

  const handleEliminar = async (id) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta encuesta?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/eliminar/${id}`, { method: 'DELETE' });
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

  const abrirModalEdicion = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/detalle/${id}`);
      if (res.ok) {
        const data = await res.json();
        setEncuestaEditando(data);
      } else {
        alert('No se pudo cargar la información completa para editar');
      }
    } catch (error) {
      console.error(error);
      alert('Error de conexión al cargar la encuesta');
    }
  };

  const handleGuardarEdicion = async (e) => {
    e.preventDefault();
    const id = encuestaEditando.id_encuesta || encuestaEditando.id;

    if (!id) {
      alert('Error: No se pudo identificar el ID de la encuesta a actualizar.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/actualizar/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(encuestaEditando)
      });

      if (res.ok) {
        alert('Encuesta actualizada correctamente');
        setEncuestaEditando(null);
        cargarEncuestas(); 
      } else {
        const errorData = await res.json();
        alert('No se pudo actualizar la encuesta: ' + (errorData.detail || 'Error desconocido'));
      }
    } catch (error) {
      console.error(error);
      alert('Error de conexión al actualizar');
    }
  };

  const toggleRedSocial = (campo, red) => {
    let actual = encuestaEditando[campo];
    let lista = [];
    if (Array.isArray(actual)) {
      lista = [...actual];
    } else if (typeof actual === 'string' && actual.trim() !== '') {
      lista = actual.split(',').map(s => s.trim());
    }

    const existe = lista.some(r => r.toLowerCase() === red.toLowerCase());
    if (existe) {
      lista = lista.filter(r => r.toLowerCase() !== red.toLowerCase());
    } else {
      lista.push(red);
    }

    setEncuestaEditando({
      ...encuestaEditando,
      [campo]: lista.join(', ')
    });
  };

  const isRedChecked = (campo, red) => {
    let actual = encuestaEditando[campo];
    if (Array.isArray(actual)) {
      return actual.some(r => String(r).toLowerCase() === red.toLowerCase());
    }
    if (typeof actual === 'string') {
      return actual.toLowerCase().includes(red.toLowerCase());
    }
    return false;
  };

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

  const descargarPDFReact = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/detalle/${id}`);
      if (!res.ok) throw new Error("No se pudo obtener el detalle");
      const datosCompletos = await res.json();

      const blob = await pdf(<EncuestaPDF datos={datosCompletos} />).toBlob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Encuesta_${id}_${datosCompletos.rut || datosCompletos.rut_empresa || 'sin_rut'}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      alert("Error al generar el PDF desde el historial");
    }
  };

  return (
    <div className="historial-container">
      <div className="historial-card">
        <h2 className="historial-title">
          {esSupervisor ? 'Historial General de Encuestas (Vista Supervisor)' : 'Historial de Encuestas'}
        </h2>

        <div className="filtros-bar">
          <div className="filtro-group">
            <label>Mes:</label>
            <select value={mesSeleccionado} onChange={(e) => setMesSeleccionado(Number(e.target.value))}>
              {NOMBRES_MESES.map((mes, idx) => (
                <option key={idx} value={idx}>{mes}</option>
              ))}
            </select>
          </div>
          <div className="filtro-group">
            <label>Año:</label>
            <select value={anioSeleccionado} onChange={(e) => setAnioSeleccionado(Number(e.target.value))}>
              {[2024, 2025, 2026, 2027].map((anio) => (
                <option key={anio} value={anio}>{anio}</option>
              ))}
            </select>
          </div>
        </div>

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
                  {esSupervisor && <th>Vendedor (ID)</th>}
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {encuestasFiltradas.map((enc) => {
                  const idEnc = enc.id_encuesta || enc.id;
                  return (
                    <tr key={idEnc}>
                      <td>{enc.empresa || enc.nombre_empresa || 'N/A'}</td>
                      <td>{enc.rut || enc.rut_empresa || 'N/A'}</td>
                      <td>{enc.encuestado || enc.nombre_encuestado || 'N/A'}</td>
                      <td>{enc.cargo || 'N/A'}</td>
                      <td>{enc.fecha || 'N/A'}</td>
                      {esSupervisor && <td>{enc.id_usuario || 'N/A'}</td>}
                      <td className="acciones-td">
                        <button className="btn-accion btn-excel" onClick={() => descargarArchivo('excel', idEnc)}>Excel</button>
                        <button className="btn-accion btn-pdf" title="Exportar a PDF" onClick={() => descargarPDFReact(idEnc)}>PDF</button>
                        <button className="btn-accion btn-editar" onClick={() => abrirModalEdicion(idEnc)}>Editar</button>
                        <button className="btn-accion btn-eliminar" onClick={() => handleEliminar(idEnc)}>Eliminar</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* edicion*/}
      {encuestaEditando && (
        <div className="modal-overlay" style={{ overflowY: 'auto', padding: '20px' }}>
          <div className="modal-content" style={{ maxWidth: '700px', margin: 'auto' }}>
            <h3>Editar Encuesta Completa</h3>
            <form onSubmit={handleGuardarEdicion}>
              
              <h4>Datos de la Empresa / Cliente</h4>
              <div className="form-group-modal">
                <label>Nombre Empresa:</label>
                <input type="text" value={encuestaEditando.empresa || encuestaEditando.nombre_empresa || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, empresa: e.target.value, nombre_empresa: e.target.value })} required />
              </div>
              <div className="form-group-modal">
                <label>RUT Empresa:</label>
                <input type="text" value={encuestaEditando.rut || encuestaEditando.rut_empresa || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, rut: e.target.value, rut_empresa: e.target.value })} />
              </div>
              <div className="form-group-modal">
                <label>Encuestado(a):</label>
                <input type="text" value={encuestaEditando.encuestado || encuestaEditando.nombre_encuestado || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, encuestado: e.target.value, nombre_encuestado: e.target.value })} required />
              </div>
              <div className="form-group-modal">
                <label>Cargo:</label>
                <input type="text" value={encuestaEditando.cargo || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, cargo: e.target.value })} />
              </div>
              <div className="form-group-modal">
                <label>Correo:</label>
                <input type="email" value={encuestaEditando.correo || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo: e.target.value })} />
              </div>
              <div className="form-group-modal">
                <label>Teléfono:</label>
                <input type="text" value={encuestaEditando.telefono || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, telefono: e.target.value })} />
              </div>
              <div className="form-group-modal">
                <label>Fecha:</label>
                <input type="date" value={encuestaEditando.fecha || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, fecha: e.target.value })} required />
              </div>

              <h4 style={{ marginTop: '15px' }}>1. Evaluación de Servicios</h4>
              {['p1_1', 'p1_2', 'p1_3'].map((p, idx) => (
                <div className="form-group-modal" key={p}>
                  <label>Pregunta 1.{idx + 1}:</label>
                  <select value={encuestaEditando[p] || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, [p]: e.target.value })}>
                    <option value="">Seleccione...</option>
                    <option value="Siempre">Siempre</option>
                    <option value="Generalmente">Generalmente</option>
                    <option value="Rara vez">Rara vez</option>
                    <option value="Nunca">Nunca</option>
                  </select>
                </div>
              ))}

              <h4 style={{ marginTop: '15px' }}>2. Evaluación de Productos</h4>
              {['p2_1', 'p2_2', 'p2_3'].map((p, idx) => (
                <div className="form-group-modal" key={p}>
                  <label>Pregunta 2.{idx + 1}:</label>
                  <select value={encuestaEditando[p] || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, [p]: e.target.value })}>
                    <option value="">Seleccione...</option>
                    <option value="Siempre">Siempre</option>
                    <option value="Generalmente">Generalmente</option>
                    <option value="Rara vez">Rara vez</option>
                    <option value="Nunca">Nunca</option>
                  </select>
                </div>
              ))}

              <h4 style={{ marginTop: '15px' }}>3. Evaluación del Personal</h4>
              {['p3_1', 'p3_2', 'p3_3'].map((p, idx) => (
                <div className="form-group-modal" key={p}>
                  <label>Pregunta 3.{idx + 1}:</label>
                  <select value={encuestaEditando[p] || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, [p]: e.target.value })}>
                    <option value="">Seleccione...</option>
                    <option value="Siempre">Siempre</option>
                    <option value="Generalmente">Generalmente</option>
                    <option value="Rara vez">Rara vez</option>
                    <option value="Nunca">Nunca</option>
                  </select>
                </div>
              ))}

              <h4 style={{ marginTop: '15px' }}>4. Redes Sociales y Otros</h4>
              
              <div className="form-group-modal">
                <label>Qué Red Social es la que más usa:</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '5px' }}>
                  {REDES_OPCIONES.map((red) => (
                    <label key={`usa-${red}`} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={isRedChecked('red_mas_usa', red) || isRedChecked('red_social_usa', red)}
                        onChange={() => toggleRedSocial('red_mas_usa', red)}
                      />
                      {red}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group-modal" style={{ marginTop: '12px' }}>
                <label>Cuál es la red Social por donde nos sigue:</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '5px' }}>
                  {REDES_OPCIONES.map((red) => (
                    <label key={`sigue-${red}`} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={isRedChecked('red_sigue', red) || isRedChecked('red_social_sigue', red)}
                        onChange={() => toggleRedSocial('red_sigue', red)}
                      />
                      {red}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group-modal" style={{ marginTop: '12px' }}>
                <label>Recibe nuestro correo Informativo:</label>
                <select
                  value={
                    String(encuestaEditando.correo_informativo) === '1' ||
                    String(encuestaEditando.correo_informativo).toUpperCase() === 'SI' ||
                    String(encuestaEditando.correo_informativo).toUpperCase() === 'TRUE'
                      ? '1'
                      : '0'
                  }
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo_informativo: Number(e.target.value) })}
                >
                  <option value="1">SI</option>
                  <option value="0">NO</option>
                </select>
              </div>

              <div className="form-group-modal" style={{ marginTop: '12px' }}>
                <label>Observaciones y Recomendaciones:</label>
                <textarea
                  rows="3"
                  style={{ width: '100%', padding: '8px', marginTop: '4px' }}
                  value={encuestaEditando.observaciones || encuestaEditando.obs_recomen || ''}
                  onChange={(e) => setEncuestaEditando({ ...encuestaEditando, observaciones: e.target.value, obs_recomen: e.target.value })}
                />
              </div>

              <div className="modal-actions" style={{ marginTop: '20px' }}>
                <button type="button" className="btn-cancelar" onClick={() => setEncuestaEditando(null)}>Cancelar</button>
                <button type="submit" className="btn-guardar-modal">Guardar Todos los Cambios</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Historial;