import React, { useRef } from "react";
import { guardarEncuesta } from "../Api/encuestaApi";
import { PDFDownloadLink } from '@react-pdf/renderer';
import EncuestaPDF from '../Components/EncuestaPDF'; 

// modulos hooks y utils
import { validarRut } from "../utils/surveyUtils";
import { useScanner } from "../hooks/useScanner";

const RellenarEncuesta = ({ onGuardadoExitoso }) => {
    const fileInputRef = useRef(null);
    
    const { procesarImagenEscaneada, isScanning, progreso } = useScanner();

    const [formData, setFormData] = React.useState({
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

    const handleFileChange = async (e) => {
        const fileOriginal = e.target.files[0];
        if (!fileOriginal) return;

        const datosEscaneados = await procesarImagenEscaneada(fileOriginal);
        if (datosEscaneados) {
            setFormData((prev) => ({ ...prev, ...datosEscaneados }));
            alert("¡Planilla escaneada con éxito! Por favor revisa los datos antes de guardar.");
        }
        
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

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
            if (name === 'rut_empresa') valorProcesado = value.replace(/[.,]/g, '');
            else if (name === 'telefono') valorProcesado = value.replace(/\D/g, '');
            else if (name === 'nombre_empresa' || name === 'nombre_encuestado') valorProcesado = value.replace(/[0-9.,]/g, '');
            else if (name === 'cargo') valorProcesado = value.replace(/[.,]/g, '');

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

        if (!validarRut(formData.rut_empresa)) {
            alert('El RUT ingresado no es válido. Por favor, verifíquelo antes de guardar.');
            return;
        }

        try {
            const datosConUsuario = { ...formData, id_usuario: idUsuarioActual || 3 };
            const result = await guardarEncuesta(datosConUsuario);

            if (result && (result.status === 'success' || result.id_encuesta)) {
                alert('Encuesta guardada con éxito');
                if (typeof onGuardadoExitoso === 'function') onGuardadoExitoso();
            } else {
                alert('Error al guardar: ' + (result?.error || 'ocurrió un problema'));
            }
        } catch (error) {
            console.error('Error al enviar la encuesta:', error);
            alert('Error de conexión con el servidor');
        }
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
                {/* apartado del scanner adaptado al diseño oscuro */}
                <section className="form-section" style={{ backgroundColor: 'var(--bg-card, #2d3748)', border: '2px dashed var(--color-accent, #4299e1)', textAlign: 'center', padding: '25px', borderRadius: '12px', marginBottom: '20px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <h3 style={{ color: 'var(--text-main, #f7fafc)' }}>Escáner de Planillas</h3>
                    <p style={{ fontSize: '14px', color: 'var(--text-muted, #a0aec0)', marginBottom: '15px' }}>
                        Sube una fotografía de la encuesta física y la Inteligencia Artificial llenará los datos por ti.
                    </p>
                    <input 
                        type="file" 
                        accept="image/*" 
                        capture="environment"
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        onChange={handleFileChange}
                    />
                    <button 
                        type="button" 
                        onClick={() => fileInputRef.current.click()} 
                        disabled={isScanning}
                        style={{ 
                            padding: '12px 24px', fontSize: '15px', fontWeight: 'bold',
                            borderRadius: '6px', cursor: isScanning ? 'not-allowed' : 'pointer', 
                            backgroundColor: isScanning ? '#4a5568' : 'var(--color-primary, #3182ce)', 
                            color: 'white', border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.2)'
                        }}
                    >
                        {isScanning ? 'Analizando imagen con IA...' : 'Tomar Foto o Subir Archivo'}
                    </button>

                    {isScanning && (
                        <div className="progress-container" style={{ marginTop: '15px', width: '100%', backgroundColor: 'var(--bg-main, #1a202c)', borderRadius: '8px', overflow: 'hidden', height: '22px', position: 'relative', border: '1px solid var(--border-color, #4a5568)' }}>
                            <div className="progress-bar" style={{ width: `${progreso}%`, height: '100%', background: 'linear-gradient(90deg, #3182ce, #63b3ed)', transition: 'width 0.4s ease' }}></div>
                            <span style={{ position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)', fontSize: '0.85rem', fontWeight: 'bold', color: '#f7fafc', lineHeight: '22px' }}>{progreso}% Procesando</span>
                        </div>
                    )}
                </section>

                <section className="form-section">
                    <h3>Datos del Cliente</h3>
                    <div className="grid-2-col">
                        <div className="form-group">
                            <label>Nombre Empresa:</label>
                            <input type="text" name="nombre_empresa" value={formData.nombre_empresa} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                RUT Empresa (Ej: 12345678-9):
                                {formData.rut_empresa && (
                                    validarRut(formData.rut_empresa) ? (
                                        <span style={{ color: '#48bb78', fontSize: '13px', fontWeight: 'bold' }}>🟢</span>
                                    ) : (
                                        <span style={{ color: '#f56565', fontSize: '13px', fontWeight: 'bold' }}>🔴 RUT incorrecto</span>
                                    )
                                )}
                            </label>
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
                                    <input type="checkbox" name="red_social_usa" value={red} checked={formData.red_social_usa.includes(red)} onChange={handleChange} />
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
                                    <input type="checkbox" name="red_social_sigue" value={red} checked={formData.red_social_sigue.includes(red)} onChange={handleChange} />
                                    {red}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Recibe nuestro correo informativo:</label>
                        <div className="checkbox-group">
                            <label>
                                <input type="radio" name="correo_informativo" value="SI" checked={formData.correo_informativo === 'SI'} onChange={handleChange} required /> SI
                            </label>
                            <label>
                                <input type="radio" name="correo_informativo" value="NO" checked={formData.correo_informativo === 'NO'} onChange={handleChange} required /> NO
                            </label>
                        </div>
                    </div>
                </section>

                <section className="form-section">
                    <h3>Observaciones y Recomendaciones</h3>
                    <textarea name="obs_recomen" rows="4" value={formData.obs_recomen} onChange={handleChange} style={{ width: '100%' }} />
                </section>

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
                                {loading ? 'Preparando PDF...' : 'Generar PDF'}
                            </button>
                        )}
                    </PDFDownloadLink>
                </div>
            </form>
        </main>
    );
};

export default RellenarEncuesta;