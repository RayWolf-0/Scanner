import React, { useState } from "react";
import { guardarEncuesta } from "../Api/encuestaApi";
import * as XLSX from 'xlsx';
import { PDFDownloadLink } from '@react-pdf/renderer';
import EncuestaPDF from '../Components/EncuestaPDF'; 

const RellenarEncuesta = ({ onGuardadoExitoso }) => {
    const [formData, setFormData] = useState({
        nombre_empresa: '',
        rut_empresa: '',
        nombre_encuestado: '',
        cargo: '',
        fecha: '',
        telefono: '',
        correo: '',
        pedidos_completos: '',
        pedidos_rapidos: '',
        respuestas_oportunas: '',
        producto_bien_presentado: '',
        producto_buena_calidad: '',
        recibe_informacion: '',
        informacion_productos_nuevos: '',
        contacto_con_ejecutivo: '',
        calidad_atencion: '',
        personal_domina_informacion: '',
        red_social_usa: [],
        red_social_sigue: [],
        correo_informativo: '',
        obs_recomen: '',
    });

    const opcionesRedes = ['Instagram', 'Tiktok', 'Facebook', 'Linkedin', 'Pinterest', 'Ninguna'];
    const opcionesEvaluacion = [
        { label: 'Siempre >90%', val: 'Siempre >90%' },
        { label: 'Generalmente 65%-89%', val: 'Generalmente 65%-89%' },
        { label: 'Rara vez 40%-64%', val: 'Rara vez 40%-64%' },
        { label: 'Nunca <40%', val: 'Nunca <40%' },
    ];

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        if (type === 'checkbox') {
            setFormData((prev) => {
                const listaActual = prev[name] || [];
                const listaActualizada = checked
                    ? [...listaActual, value]
                    : listaActual.filter((item) => item !== value);

                return { ...prev, [name]: listaActualizada };
            });
        } else {
            let valorProcesado = value;

            if (name === 'rut_empresa') {
                valorProcesado = value.replace(/\./g, '');
            }
            else if (name === 'telefono') {
                valorProcesado = value.replace(/\D/g, '');
            }
            else if (name === 'nombre_empresa' || name === 'nombre_encuestado') {
                valorProcesado = value.replace(/[0-9]/g, '');
            }

            setFormData((prev) => ({ ...prev, [name]: valorProcesado }));
        }
    };

    let idUsuarioActual = null;
    let nombreUsuario = 'Usuario Desconocido';
    try {
        const usuarioGuardado = localStorage.getItem('usuario_tecbolt');
        if (usuarioGuardado) {
            const usuarioObj = JSON.parse(usuarioGuardado);
            idUsuarioActual = usuarioObj.id_usuario || usuarioObj.id || usuarioObj.userId;
            nombreUsuario = usuarioObj.username || usuarioObj.user || usuarioObj.nombre || 'Usuario Desconocido';
        }
    } catch (error) {
        console.error("Error leyendo el usuario de localStorage", error);
    }

const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const datosConUsuario = {
                ...formData,
                id_usuario: idUsuarioActual || 3 
            };

            const result = await guardarEncuesta(datosConUsuario);

            if (result && (result.status === 'success' || result.id_encuesta)) {
                alert('Encuesta guardada con éxito');

                if (typeof onGuardadoExitoso === 'function') {
                    onGuardadoExitoso();
                }
            } else {
                alert('Error al guardar: ' + (result?.error || 'ocurrió un problema'));
            }
        } catch (error) {
            console.error('Error al enviar la encuesta:', error);
            alert('Error de conexión con el servidor');
        }
    };
    const handleGenerarExcel = () => {
        const datosExcel = [
            { "Campo": "--- DATOS DEL CLIENTE ---", "Valor": "" },
            { "Campo": "Nombre Empresa", "Valor": formData.nombre_empresa || '' },
            { "Campo": "RUT Empresa", "Valor": formData.rut_empresa || '' },
            { "Campo": "Nombre Encuestado", "Valor": formData.nombre_encuestado || '' },
            { "Campo": "Cargo", "Valor": formData.cargo || '' },
            { "Campo": "Fecha", "Valor": formData.fecha || '' },
            { "Campo": "Teléfono", "Valor": formData.telefono || '' },
            { "Campo": "Correo", "Valor": formData.correo || '' },
            {},
            { "Campo": "--- 1. EVALUACIÓN DE SERVICIOS ---", "Valor": "" },
            { "Campo": "Pedidos Completos", "Valor": formData.pedidos_completos || '' },
            { "Campo": "Pedidos Rápidos (24-48 hrs)", "Valor": formData.pedidos_rapidos || '' },
            { "Campo": "Respuestas Oportunas", "Valor": formData.respuestas_oportunas || '' },
            {},
            { "Campo": "--- 2. EVALUACIÓN DE PRODUCTOS ---", "Valor": "" },
            { "Campo": "Producto Bien Presentado", "Valor": formData.producto_bien_presentado || '' },
            { "Campo": "Producto Buena Calidad", "Valor": formData.producto_buena_calidad || '' },
            { "Campo": "Recibe Información Compras", "Valor": formData.recibe_informacion || '' },
            { "Campo": "Información Productos Nuevos", "Valor": formData.informacion_productos_nuevos || '' },
            {},
            { "Campo": "--- 3. EVALUACIÓN DEL PERSONAL ---", "Valor": "" },
            { "Campo": "Contacto con Ejecutivo", "Valor": formData.contacto_con_ejecutivo || '' },
            { "Campo": "Calidad de Atención", "Valor": formData.calidad_atencion || '' },
            { "Campo": "Personal Domina Información", "Valor": formData.personal_domina_informacion || '' },
            {},
            { "Campo": "--- 4. REDES SOCIALES ---", "Valor": "" },
            { "Campo": "Red Social que más usa", "Valor": Array.isArray(formData.red_social_usa) ? formData.red_social_usa.join(', ') : '' },
            { "Campo": "Red Social por donde nos sigue", "Valor": Array.isArray(formData.red_social_sigue) ? formData.red_social_sigue.join(', ') : '' },
            { "Campo": "Recibe Correo Informativo", "Valor": formData.correo_informativo || '' },
            {},
            { "Campo": "--- OBSERVACIONES Y RECOMENDACIONES ---", "Valor": "" },
            { "Campo": "Observaciones", "Valor": formData.obs_recomen || '' }
        ];

        const worksheet = XLSX.utils.json_to_sheet(datosExcel);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Encuesta");

        XLSX.writeFile(workbook, `Encuesta_${formData.nombre_empresa || 'Cliente'}.xlsx`);
    }; 

    const datosParaPDF = {
        empresa: formData.nombre_empresa,
        rut: formData.rut_empresa,
        encuestado: formData.nombre_encuestado,
        cargo: formData.cargo,
        correo: formData.correo,
        telefono: formData.telefono,
        fecha: formData.fecha,
        p1_1: formData.pedidos_completos?.split(' ')[0] || '', 
        p1_2: formData.pedidos_rapidos?.split(' ')[0] || '',
        p1_3: formData.respuestas_oportunas?.split(' ')[0] || '',
        p2_1: formData.producto_bien_presentado?.split(' ')[0] || '',
        p2_2: formData.producto_buena_calidad?.split(' ')[0] || '',
        p2_3: formData.informacion_productos_nuevos?.split(' ')[0] || '',
        p3_1: formData.contacto_con_ejecutivo?.split(' ')[0] || '',
        p3_2: formData.calidad_atencion?.split(' ')[0] || '',
        p3_3: formData.personal_domina_informacion?.split(' ')[0] || '',
        rs_instagram: formData.red_social_usa.includes('Instagram') || formData.red_social_sigue.includes('Instagram'),
        rs_tiktok: formData.red_social_usa.includes('Tiktok') || formData.red_social_sigue.includes('Tiktok'),
        rs_facebook: formData.red_social_usa.includes('Facebook') || formData.red_social_sigue.includes('Facebook'),
        rs_linkedin: formData.red_social_usa.includes('Linkedin') || formData.red_social_sigue.includes('Linkedin'),
        rs_pinterest: formData.red_social_usa.includes('Pinterest') || formData.red_social_sigue.includes('Pinterest'),
        rs_ninguna: formData.red_social_usa.includes('Ninguna') || formData.red_social_sigue.includes('Ninguna'),
        red_mas_usa: formData.red_social_usa.join(', '),
        red_sigue: formData.red_social_sigue.join(', '),
        correo_informativo: formData.correo_informativo,
        observaciones: formData.obs_recomen,
        usuario: nombreUsuario
    };

    return (
        <main className="content">
            <header>
                <h1>Rellenar Encuesta de Satisfacción 2026</h1>
            </header>

            <form id="encuesta-form-container" onSubmit={handleSubmit} className="survey-form">

                <section className="form-section">
                    <h3>Datos del Cliente</h3>
                    <div className="grid-2-col">
                        <div className="form-group">
                            <label>Nombre Empresa:</label>
                            <input type="text" name="nombre_empresa" value={formData.nombre_empresa} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>RUT Empresa (Sin puntos):</label>
                            <input type="text" name="rut_empresa" value={formData.rut_empresa} onChange={handleChange} placeholder="Ej: 12345678-9" required />
                        </div>
                        <div className="form-group">
                            <label>Nombre Encuestado(a):</label>
                            <input type="text" name="nombre_encuestado" value={formData.nombre_encuestado} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Cargo:</label>
                            <input type="text" name="cargo" value={formData.cargo} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Fecha:</label>
                            <input type="date" name="fecha" value={formData.fecha} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Teléfono (Solo números):</label>
                            <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Correo:</label>
                            <input type="email" name="correo" value={formData.correo} onChange={handleChange} required />
                        </div>
                    </div>
                </section>

                <section className="form-section">
                    <h3>1. Evaluación de Servicios Entregados</h3>
                    <table className="survey-table">
                        <thead>
                            <tr>
                                <th>Pregunta</th>
                                {opcionesEvaluacion.map((op, i) => <th key={i}>{op.label}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Recibe sus pedidos completos</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="pedidos_completos" value={op.val} checked={formData.pedidos_completos === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe sus pedidos rápidamente (24-48 horas)</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="pedidos_rapidos" value={op.val} checked={formData.pedidos_rapidos === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Obtiene respuesta oportuna ante reclamos, consultas y requerimientos adicionales</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="respuestas_oportunas" value={op.val} checked={formData.respuestas_oportunas === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                <section className="form-section">
                    <h3>2. Evaluación de Productos Comprados</h3>
                    <table className="survey-table">
                        <thead>
                            <tr>
                                <th>Pregunta</th>
                                {opcionesEvaluacion.map((op, i) => <th key={i}>{op.label}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>El producto está bien presentado (aspecto visual)</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="producto_bien_presentado" value={op.val} checked={formData.producto_bien_presentado === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>El producto es de buena calidad</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="producto_buena_calidad" value={op.val} checked={formData.producto_buena_calidad === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe información sobre sus compras</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="recibe_informacion" value={op.val} checked={formData.recibe_informacion === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe información de productos nuevos, variedad y alternativas</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="informacion_productos_nuevos" value={op.val} checked={formData.informacion_productos_nuevos === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                <section className="form-section">
                    <h3>3. Evaluación del Personal</h3>
                    <table className="survey-table">
                        <thead>
                            <tr>
                                <th>Pregunta</th>
                                {opcionesEvaluacion.map((op, i) => <th key={i}>{op.label}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Recibe contacto permanente de su ejecutivo</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="contacto_con_ejecutivo" value={op.val} checked={formData.contacto_con_ejecutivo === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>La calidad de la atención proporcionada es buena</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="calidad_atencion" value={op.val} checked={formData.calidad_atencion === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>El personal tiene dominio de información técnica</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="personal_domina_informacion" value={op.val} checked={formData.personal_domina_informacion === op.val} onChange={handleChange} required />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                <section className="form-section">
                    <h3>4. Redes Sociales (puede marcar más de una opción)</h3>

                    <div className="form-group" style={{ marginBottom: '15px' }}>
                        <label>¿Qué red social es la que más usa?</label>
                        <div className="checkbox-group">
                            {opcionesRedes.map((red) => (
                                <label key={`usa-${red}`}>
                                    <input
                                        type="checkbox"
                                        name="red_social_usa"
                                        value={red}
                                        checked={formData.red_social_usa.includes(red)}
                                        onChange={handleChange}
                                    />
                                    {red}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="form-group" style={{ marginBottom: '15px' }}>
                        <label>¿Cuál es la red social por dónde nos sigue?</label>
                        <div className="checkbox-group">
                            {opcionesRedes.map((red) => (
                                <label key={`sigue-${red}`}>
                                    <input
                                        type="checkbox"
                                        name="red_social_sigue"
                                        value={red}
                                        checked={formData.red_social_sigue.includes(red)}
                                        onChange={handleChange}
                                    />
                                    {red}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Recibe nuestro correo informativo:</label>
                        <div className="checkbox-group">
                            <label>
                                <input
                                    type="radio"
                                    name="correo_informativo"
                                    value="SI"
                                    checked={formData.correo_informativo === 'SI'}
                                    onChange={handleChange}
                                    required
                                /> SI
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name="correo_informativo"
                                    value="NO"
                                    checked={formData.correo_informativo === 'NO'}
                                    onChange={handleChange}
                                    required
                                /> NO
                            </label>
                        </div>
                    </div>
                </section>

                <section className="form-section">
                    <h3>Observaciones y Recomendaciones</h3>
                    <textarea
                        name="obs_recomen"
                        rows="4"
                        value={formData.obs_recomen}
                        onChange={handleChange}
                        style={{ width: '100%' }}
                    />
                </section>

                {/* Botones de acción perfectamente uniformes y alineados */}
                <div style={{ display: 'flex', gap: '15px', marginTop: '20px', alignItems: 'stretch' }}>
                    <button type="submit" className="btn-submit" style={{ flex: 1, padding: '12px 15px', fontSize: '14px', borderRadius: '6px', textAlign: 'center', cursor: 'pointer' }}>
                        Guardar Encuesta
                    </button>

                    <PDFDownloadLink 
                        document={<EncuestaPDF datos={datosParaPDF} />} 
                        fileName={`Encuesta_${formData.nombre_empresa || 'Cliente'}.pdf`}
                        style={{ flex: 1, textDecoration: 'none', display: 'flex' }}
                    >
                        {({ loading }) => (
                            <button type="button" className="btn-submit" disabled={loading} style={{ width: '100%', padding: '12px 15px', fontSize: '14px', borderRadius: '6px', textAlign: 'center', cursor: 'pointer' }}>
                                {loading ? 'Preparando PDF...' : 'Generar PDF Local'}
                            </button>
                        )}
                    </PDFDownloadLink>

                    <button type="button" className="btn-submit" onClick={handleGenerarExcel} style={{ flex: 1, padding: '12px 15px', fontSize: '14px', borderRadius: '6px', textAlign: 'center', cursor: 'pointer' }}>
                        Generar Excel Local
                    </button>
                </div>
            </form>
        </main>
    );
};

export default RellenarEncuesta;