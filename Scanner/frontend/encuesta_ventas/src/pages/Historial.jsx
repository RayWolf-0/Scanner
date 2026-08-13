import React, { useState, useEffect } from 'react';
import { pdf } from '@react-pdf/renderer';
import * as XLSX from 'xlsx';
import EncuestaPDF from '../Components/EncuestaPDF';

const NOMBRES_MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const REDES_OPCIONES = ['Instagram', 'TikTok', 'Facebook', 'LinkedIn', 'Pinterest', 'Ninguna'];

const API_BASE_URL = '/api/encuesta';

// Función para editar el PDF
const getVendedorNombre = (e) => {
  if (!e) return 'Desconocido';
  
  // coloca el user
  if (e.username) return e.username;
  if (e.user) return e.user;
  
  if (e.usuario && e.usuario !== 'Vendedor') return e.usuario; 
  
  // coloca el nombre si no encuentra el user (no debería de pasar :b)
  if (e.nombre) return `${e.nombre} ${e.apellido || ''}`.trim();
  if (e.nombre_vendedor) return e.nombre_vendedor;
  if (e.vendedor) return e.vendedor;

  // id
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

  const toggleRedSocial = (campo, red) => {
    let actual = encuestaEditando[campo];
    let lista = Array.isArray(actual) ? [...actual] : (typeof actual === 'string' && actual.trim() !== '' ? actual.split(',').map(s => s.trim()) : []);
    const existe = lista.some(r => r.toLowerCase() === red.toLowerCase());
    lista = existe ? lista.filter(r => r.toLowerCase() !== red.toLowerCase()) : [...lista, red];
    setEncuestaEditando({ ...encuestaEditando, [campo]: lista.join(', ') });
  };

  const isRedChecked = (campo, red) => {
    let actual = encuestaEditando[campo];
    if (Array.isArray(actual)) return actual.some(r => String(r).toLowerCase() === red.toLowerCase());
    if (typeof actual === 'string') return actual.toLowerCase().includes(red.toLowerCase());
    return false;
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

  const generarExcelAutomatizado = async () => {
    if (encuestasFiltradas.length === 0) return alert("No hay encuestas para exportar.");
    setExportando(true);

    try {
      const encuestasCompletas = await Promise.all(
        encuestasFiltradas.map(async (enc) => {
          const id = enc.id_encuesta || enc.id;
          try {
            const res = await fetch(`${API_BASE_URL}/detalle/${id}`, { cache: 'no-store' });
            if (res.ok) {
              const detalle = await res.json();
              return { ...enc, ...detalle }; 
            }
          } catch (err) {
            console.error("Error trayendo detalle", id);
          }
          return enc;
        })
      );

      const colL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
      const cols = [];
      for(let i=0; i<26; i++) cols.push(colL[i]);
      for(let i=0; i<26; i++) { for(let j=0; j<26; j++) cols.push(colL[i]+colL[j]); }

      const h1 = new Array(56).fill("");
      h1[5] = "P1: SERVICIOS";
      h1[17] = "P2: PRODUCTOS";
      h1[29] = "P3: PERSONAL";
      h1[41] = "REDES SOCIALES";

      const h2 = new Array(56).fill("");
      h2[0] = "Datos del Cliente";
      h2[5] = "p1_1 (Pedidos completos)";
      h2[9] = "p1_2 (Pedidos rápidos)";
      h2[13] = "p1_3 (Respuestas reclamos)";
      h2[17] = "p2_1 (Visual producto)";
      h2[21] = "p2_2 (Calidad producto)";
      h2[25] = "p2_3 (Nuevos productos)";
      h2[29] = "p3_1 (Info variedades)";
      h2[33] = "p3_2 (Calidad atención)";
      h2[37] = "p3_3 (Dominio técnico)";
      h2[41] = "red_mas_usa";
      h2[47] = "red_sigue";
      h2[53] = "correo_informativo";

      const h3 = [
        "Nº", "RUT", "Empresa", "Vendedor", "Fecha",
        ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%",
        ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%",
        ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%", ">90%", "65-89%", "40-64%", "<40%",
        "Inst", "Tik", "Face", "Link", "Pin", "Nin",
        "Inst", "Tik", "Face", "Link", "Pin", "Nin",
        "SI", "NO", "TOTAL FILA"
      ];

      const aoa = [h1, h2, h3];
      
      const getEv = (val) => {
        const str = String(val || '').toLowerCase();
        let arr = ["","","",""];
        if (str.includes('siempre')) arr[0] = 1;
        else if (str.includes('generalmente')) arr[1] = 1;
        else if (str.includes('rara')) arr[2] = 1;
        else if (str.includes('nunca')) arr[3] = 1;
        return arr;
      };

      const getSoc = (valArray, valString) => {
        let str = "";
        if (Array.isArray(valArray)) { str = valArray.join(' ').toLowerCase(); }
        else { str = String(valString || valArray || '').toLowerCase(); }
        return [
          str.includes('instagram') ? 1 : "",
          str.includes('tiktok') ? 1 : "",
          str.includes('facebook') ? 1 : "",
          str.includes('linkedin') ? 1 : "",
          str.includes('pinterest') ? 1 : "",
          str.includes('ninguna') ? 1 : ""
        ];
      };

      const getCor = (val) => {
        if (val == null || val == undefined) return ["",""];
        const str = String(val).trim().toUpperCase();
        if (str === 'SI' || str === '1' || str === 'TRUE') return [1, ""];
        if (str === 'NO' || str === '0' || str === 'FALSE') return ["", 1];
        return ["", ""];
      };

      encuestasCompletas.forEach((enc, index) => {
         const rowNum = 4 + index; 
         let row = [
            index + 1, 
            enc.rut_empresa || enc.rut || '',
            enc.nombre_empresa || enc.empresa || '',
            getVendedorNombre(enc),
            enc.fecha || '',
            ...getEv(enc.p1_1 || enc.pedidos_completos),
            ...getEv(enc.p1_2 || enc.pedidos_rapidos),
            ...getEv(enc.p1_3 || enc.respuestas_oportunas),
            ...getEv(enc.p2_1 || enc.producto_bien_presentado),
            ...getEv(enc.p2_2 || enc.producto_buena_calidad),
            ...getEv(enc.p2_3 || enc.informacion_productos_nuevos),
            ...getEv(enc.p3_1 || enc.contacto_con_ejecutivo),
            ...getEv(enc.p3_2 || enc.calidad_atencion),
            ...getEv(enc.p3_3 || enc.personal_domina_informacion),
            ...getSoc(enc.red_social_usa, enc.red_mas_usa),
            ...getSoc(enc.red_social_sigue, enc.red_sigue),
            ...getCor(enc.correo_informativo)
         ];
         row[55] = { t: 'n', f: `SUM(F${rowNum}:BC${rowNum})` };
         aoa.push(row);
      });

      const totalRowIndex = 4 + encuestasCompletas.length; 
      let sum1 = new Array(56).fill("");
      sum1[4] = "TOTALES DE COLUMNA:";
      for(let c = 5; c <= 55; c++) {
          const cL = cols[c];
          sum1[c] = { t: 'n', f: `SUM(${cL}4:${cL}${totalRowIndex-1})` };
      }
      aoa.push(sum1);

      const ws = XLSX.utils.aoa_to_sheet(aoa);
      const wscols = [{ wpx: 30 }, { wpx: 90 }, { wpx: 160 }, { wpx: 90 }, { wpx: 80 }];
      for (let i = 0; i < 50; i++) wscols.push({ wpx: 25 }); 
      wscols.push({ wpx: 60 }); 
      ws['!cols'] = wscols;

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "Resumen Encuestas");
      XLSX.writeFile(wb, `Resumen_Encuestas_${vendedorFiltro}.xlsx`);

    } catch (error) {
      alert("Hubo un error al extraer los datos detallados.");
      console.error(error);
    } finally {
      setExportando(false);
    }
  };

  return (
    <div className="historial-container">
      <div className="historial-card">
        <h2 className="historial-title">
          {esSupervisor ? 'Historial General de Encuestas' : 'Historial de Encuestas'}
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
          {esSupervisor && (
            <div className="filtro-group">
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
                          <button className="btn-accion btn-pdf" onClick={() => descargarPDFReact(idEnc)}>PDF</button>
                          <button className="btn-accion btn-editar" onClick={() => abrirModalEdicion(idEnc)}>Editar</button>
                          <button className="btn-accion btn-eliminar" onClick={() => handleEliminar(idEnc)}>Eliminar</button>
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
              className="btn-accion btn-excel" 
              style={{ padding: '10px 15px', fontWeight: 'bold' }} 
              onClick={generarExcelAutomatizado}
              disabled={exportando}
            >
              {exportando ? "Generando Excel..." : "Descargar Excel"}
            </button>
          </div>
        )}
      </div>

      {/* Modal de edición */}
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
                      <input type="checkbox" checked={isRedChecked('red_mas_usa', red) || isRedChecked('red_social_usa', red)} onChange={() => toggleRedSocial('red_mas_usa', red)} />
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
                      <input type="checkbox" checked={isRedChecked('red_sigue', red) || isRedChecked('red_social_sigue', red)} onChange={() => toggleRedSocial('red_sigue', red)} />
                      {red}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group-modal" style={{ marginTop: '12px' }}>
                <label>Recibe nuestro correo Informativo:</label>
                <select value={String(encuestaEditando.correo_informativo) === '1' || String(encuestaEditando.correo_informativo).toUpperCase() === 'SI' || String(encuestaEditando.correo_informativo).toUpperCase() === 'TRUE' ? '1' : '0'} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo_informativo: Number(e.target.value) })}>
                  <option value="1">SI</option>
                  <option value="0">NO</option>
                </select>
              </div>

              <div className="form-group-modal" style={{ marginTop: '12px' }}>
                <label>Observaciones y Recomendaciones:</label>
                <textarea rows="3" style={{ width: '100%', padding: '8px', marginTop: '4px' }} value={encuestaEditando.observaciones || encuestaEditando.obs_recomen || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, observaciones: e.target.value, obs_recomen: e.target.value })} />
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