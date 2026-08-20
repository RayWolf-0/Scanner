import React, { useState, useEffect } from 'react';
import { pdf } from '@react-pdf/renderer';
import EncuestaPDF from '../Components/EncuestaPDF';
import EditarEncuestaModal from '../Components/EditarEncuestaModal';
import { generarExcelAutomatizado } from '../utils/excelUtils';
import styles from './Historial.module.css';

const NOMBRES_MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const API_BASE_URL = '/api/encuesta';

const getVendedorNombre = (e) => {
  if (!e) return 'Desconocido';
  if (e.username) return e.username;
  if (e.user) return e.user;
  if (e.usuario && e.usuario !== 'Vendedor') return e.usuario; 
  if (e.nombre) return `${e.nombre} ${e.apellido || ''}`.trim();
  if (e.nombre_vendedor) return e.nombre_vendedor;
  if (e.vendedor) return e.vendedor;
  return e.id_usuario || 'Desconocido';
};

const Historial = ({ usuario }) => {
  const [encuestas, setEncuestas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [exportando, setExportando] = useState(false); 

  const usuarioGuardado = JSON.parse(localStorage.getItem('usuario_tecbolt') || '{}');
  const datosUsr = usuario?.usuario || usuario || usuarioGuardado;
  const rolVal = datosUsr?.rol !== undefined ? datosUsr.rol : datosUsr?.id_rol;
  const textoRol = String(rolVal || '').toLowerCase();
  const esSupervisor = Number(rolVal) === 2 || textoRol.includes('super');
  const idUsuarioActual = datosUsr?.id_usuario || datosUsr?.id || datosUsr?.userId || usuarioGuardado.id_usuario || usuarioGuardado.id;

  const hoy = new Date();
  const [mesSeleccionado, setMesSeleccionado] = useState(hoy.getMonth());
  const [anioSeleccionado, setAnioSeleccionado] = useState(hoy.getFullYear());
  const [vendedorFiltro, setVendedorFiltro] = useState('todos');
  const [encuestaEditando, setEncuestaEditando] = useState(null);

  const parseFechaLocal = (fechaStr) => {
    if (!fechaStr) return null;
    const partes = String(fechaStr).split('T')[0].split('-');
    if (partes.length === 3) return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    return new Date(fechaStr);
  };

  const cargarEncuestas = async () => {
    setCargando(true);
    try {
      const res = await fetch(`${API_BASE_URL}/listar`, { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        setEncuestas(Array.isArray(data) ? data : (data.encuestas || []));
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

  const vendedoresUnicos = Array.from(new Set(encuestas.map(getVendedorNombre))).filter(Boolean);

  const encuestasFiltradas = encuestas.filter((e) => {
    if (!e.fecha) return false;
    const fechaObj = parseFechaLocal(e.fecha);
    if (!fechaObj || isNaN(fechaObj.getTime())) return false;

    const coincideMesAnio = fechaObj.getMonth() === Number(mesSeleccionado) && fechaObj.getFullYear() === Number(anioSeleccionado);
    const vendedorEnc = getVendedorNombre(e);
    const coincideUsuario = esSupervisor 
      ? (vendedorFiltro === 'todos' || String(vendedorEnc) === String(vendedorFiltro))
      : (idUsuarioActual && e.id_usuario ? Number(e.id_usuario) === Number(idUsuarioActual) : true); 

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
      console.error('Error al conectar con el servidor');
    }
  };

  const abrirModalEdicion = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/detalle/${id}`);
      if (res.ok) setEncuestaEditando(await res.json());
      else alert('No se pudo cargar la información completa para editar');
    } catch (error) {
      alert('Error de conexión al cargar la encuesta');
    }
  };

  const handleGuardarEdicion = async (e) => {
    e.preventDefault();
    const id = encuestaEditando.id_encuesta || encuestaEditando.id;
    if (!id) return alert('Error: No se pudo identificar el ID.');

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
        alert('No se pudo actualizar la encuesta');
      }
    } catch (error) {
      alert('Error de conexión al actualizar');
    }
  };

  const descargarPDFReact = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/detalle/${id}`, { cache: 'no-store' });
      if (!res.ok) throw new Error();
      const datosCompletos = await res.json();

      const encuestaEnLista = encuestas.find(e => (e.id_encuesta || e.id) === id);
      const vendedorReal = getVendedorNombre(encuestaEnLista || datosCompletos);

      const usaStr = String(datosCompletos.red_mas_usa || datosCompletos.red_social_usa || '').toLowerCase();
      const sigueStr = String(datosCompletos.red_sigue || datosCompletos.red_social_sigue || '').toLowerCase();

      let correoInfo = 'NO'; 
      if (datosCompletos.correo_informativo !== undefined && datosCompletos.correo_informativo !== null) {
          const valCorreo = String(datosCompletos.correo_informativo).trim().toUpperCase();
          if (valCorreo === '1' || valCorreo === 'SI' || valCorreo === 'TRUE') correoInfo = 'SI';
          if (valCorreo === '0' || valCorreo === 'NO' || valCorreo === 'FALSE') correoInfo = 'NO';
      }

      const datosParaPDF = {
          empresa: datosCompletos.empresa || datosCompletos.nombre_empresa || '',
          rut: datosCompletos.rut || datosCompletos.rut_empresa || '',
          encuestado: datosCompletos.encuestado || datosCompletos.nombre_encuestado || '',
          cargo: datosCompletos.cargo || '',
          correo: datosCompletos.correo || '',
          telefono: datosCompletos.telefono || '',
          fecha: datosCompletos.fecha || '',
          p1_1: String(datosCompletos.p1_1 || datosCompletos.pedidos_completos || '').split(' ')[0], 
          p1_2: String(datosCompletos.p1_2 || datosCompletos.pedidos_rapidos || '').split(' ')[0],
          p1_3: String(datosCompletos.p1_3 || datosCompletos.respuestas_oportunas || '').split(' ')[0],
          p2_1: String(datosCompletos.p2_1 || datosCompletos.producto_bien_presentado || '').split(' ')[0],
          p2_2: String(datosCompletos.p2_2 || datosCompletos.producto_buena_calidad || '').split(' ')[0],
          p2_3: String(datosCompletos.p2_3 || datosCompletos.informacion_productos_nuevos || '').split(' ')[0],
          p3_1: String(datosCompletos.p3_1 || datosCompletos.contacto_con_ejecutivo || '').split(' ')[0],
          p3_2: String(datosCompletos.p3_2 || datosCompletos.calidad_atencion || '').split(' ')[0],
          p3_3: String(datosCompletos.p3_3 || datosCompletos.personal_domina_informacion || '').split(' ')[0],
          rs_instagram: usaStr.includes('instagram') || sigueStr.includes('instagram'),
          rs_tiktok: usaStr.includes('tiktok') || sigueStr.includes('tiktok'),
          rs_facebook: usaStr.includes('facebook') || sigueStr.includes('facebook'),
          rs_linkedin: usaStr.includes('linkedin') || sigueStr.includes('linkedin'),
          rs_pinterest: usaStr.includes('pinterest') || sigueStr.includes('pinterest'),
          rs_ninguna: usaStr.includes('ninguna') || sigueStr.includes('ninguna'),
          red_mas_usa: datosCompletos.red_mas_usa || datosCompletos.red_social_usa || '',
          red_sigue: datosCompletos.red_sigue || datosCompletos.red_social_sigue || '',
          correo_informativo: correoInfo,
          observaciones: datosCompletos.observaciones || datosCompletos.obs_recomen || '',
          usuario: vendedorReal 
      };

      const blob = await pdf(<EncuestaPDF datos={datosParaPDF} />).toBlob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `Encuesta_${id}.pdf`;
      document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
    } catch (error) {
      alert("Error al generar el PDF desde el historial");
    }
  };

  return (
    <div className={styles.historialContainer}>
      <div className={styles.historialCard}>
        <h2 className={styles.historialTitle}>
          {esSupervisor ? 'Historial General de Encuestas' : 'Historial de Encuestas'}
        </h2>

        <div className={styles.filtrosBar}>
          <div className={styles.filtroGroup}>
            <label>Mes:</label>
            <select value={mesSeleccionado} onChange={(e) => setMesSeleccionado(Number(e.target.value))}>
              {NOMBRES_MESES.map((mes, idx) => (
                <option key={idx} value={idx}>{mes}</option>
              ))}
            </select>
          </div>
          <div className={styles.filtroGroup}>
            <label>Año:</label>
            <select value={anioSeleccionado} onChange={(e) => setAnioSeleccionado(Number(e.target.value))}>
              {[2024, 2025, 2026, 2027].map((anio) => (
                <option key={anio} value={anio}>{anio}</option>
              ))}
            </select>
          </div>
          {esSupervisor && (
            <div className={styles.filtroGroup}>
              <label>Vendedor:</label>
              <select value={vendedorFiltro} onChange={(e) => setVendedorFiltro(e.target.value)}>
                <option value="todos">Todos los usuarios</option>
                {vendedoresUnicos.map((v, idx) => (
                  <option key={idx} value={v}>{v}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {cargando ? (
          <p className={styles.statusMsg}>Cargando encuestas...</p>
        ) : encuestasFiltradas.length === 0 ? (
          <p className={styles.statusMsg}>No hay encuestas registradas en {NOMBRES_MESES[mesSeleccionado]} {anioSeleccionado}.</p>
        ) : (
          <div className={styles.tablaResponsive}>
            <table className={styles.tablaHistorial}>
              <thead>
                <tr>
                  <th>Empresa</th>
                  <th>RUT</th>
                  <th>Encuestado</th>
                  <th>Cargo</th>
                  <th>Fecha</th>
                  {esSupervisor && <th>Vendedor</th>}
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
                      {esSupervisor && <td>{getVendedorNombre(enc)}</td>}
                      
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', gap: '5px', justifyContent: 'center' }}>
                          <button className={`${styles.btnAccion} ${styles.btnPdf}`} onClick={() => descargarPDFReact(idEnc)}>PDF</button>
                          <button className={`${styles.btnAccion} ${styles.btnEditar}`} onClick={() => abrirModalEdicion(idEnc)}>Editar</button>
                          <button className={`${styles.btnAccion} ${styles.btnEliminar}`} onClick={() => handleEliminar(idEnc)}>Eliminar</button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        
        {esSupervisor && encuestasFiltradas.length > 0 && (
          <div style={{ marginTop: '20px', textAlign: 'right' }}>
            <button 
              className={`${styles.btnAccion} ${styles.btnExcel}`} 
              style={{ padding: '10px 15px', fontWeight: 'bold' }} 
              onClick={() => generarExcelAutomatizado(encuestasFiltradas, vendedorFiltro, API_BASE_URL, getVendedorNombre, setExportando)}
              disabled={exportando}
            >
              {exportando ? "Generando Excel..." : "Descargar Excel"}
            </button>
          </div>
        )}
      </div>

      <EditarEncuestaModal 
        encuestaEditando={encuestaEditando}
        setEncuestaEditando={setEncuestaEditando}
        handleGuardarEdicion={handleGuardarEdicion}
        onCerrar={() => setEncuestaEditando(null)}
      />
    </div>
  );
};

export default Historial;