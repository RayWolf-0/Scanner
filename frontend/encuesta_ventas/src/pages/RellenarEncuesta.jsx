import React, { useState } from "react";
import { guardarEncuesta } from "../Api/encuestaApi";

const RellenarEncuesta = () => {
    const [formData, setFormData] = useState({
        nombre_empresa: '',
        rut_empresa: '',
        nombre_encuestado: '',
        cargo: '',
        fecha: '',
        telefono: '',
        correo:'',
        pedidos_completos:'',
        pedidos_rapidos:'',
        respuestas_oportunas:'',
        producto_bien_presentado:'',
        producto_buena_calidad:'',
        recibe_informacion:'',
        informacion_productos_nuevos:'',
        contacto_con_ejecutivo:'',
        calidad_atencion:'',
        personal_domina_informacion:'',
        red_social_usa:[], //varias opciones
        red_social_sigue:[], //varias opciones
        correo_informativo:'',
        obs_recomen:'',
    });

    const opcionesRedes = ['Instagram', 'Tiktok', 'Facebook', 'Linkedin', 'Pinterest', 'Ninguna'];
    const opcionesEvaluacion = [
        {label: 'Siempre >90%', val: 'Siempre >90%'},
        {label: 'Generalmente 65%-89%', val: 'Generalmente 65%-89%'},
        {label: 'Rara vez 40%-64%', val: 'Rara vez 40%-64%'},
        {label: 'Nunca <40%', val: 'Nunca <40%'},
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
            setFormData((prev) => ({ ...prev, [name]: value }));
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        try{
            const result = guardarEncuesta(formData);
            if (result.status == 'success'){
                alert('Encuesta Guardada');
                if (result.id_encuesta){
                    window.open('/api/encuesta/exportar/pdf/${result.id_encuesta');
                    window.open('/api/encuesta/exportar/excel/${result.id_encuesta');
                }
            }else{
                alert('Error al guardar: ' + (result.error || 'ocurrió un problema'));
            }
        } catch (error){
            console.error('Error al enviar la encuesta')
            alert('Error de Conexión');
        }
    };

    return(
        <main className="content">
            <header>
                <h1>Rellenar Encuesta de Satisfacción 2026</h1>
            </header>

            <form onSubmit={handleSubmit} className="survey-form">
                
                {/*Datos del Cliente*/}
                <section className="form-section">
                    <h3>Datos del Cliente</h3>
                    <div className="grid-2-col">
                        <div className="form-group">
                            <label>Nombre Empresa:</label>
                            <input type="text" name="nombre_empresa" value={formData.nombre_empresa} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>RUT Empresa:</label>
                            <input type="text" name="rut_empresa" value={formData.rut_empresa} onChange={handleChange} required />
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
                            <label>Teléfono:</label>
                            <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Correo:</label>
                            <input type="email" name="correo" value={formData.correo} onChange={handleChange} required />
                        </div>
                    </div>
                </section>

                {/* Evaluación de Servicos Entregados*/}
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
                                        <input type="radio" name="pedidos_completos" value={op.val} checked={formData.pedidos_completos === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe sus pedidos rápidamente (24-48 horas)</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="pedidos_rapidos" value={op.val} checked={formData.pedidos_rapidos === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Obtiene respuesta oportuna ante reclamos, consultas y requerimientos adicionales</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="respuestas_oportunas" value={op.val} checked={formData.respuestas_oportunas === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                {/* Evaluacion de Productos Comprados*/}
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
                                        <input type="radio" name="producto_bien_presentado" value={op.val} checked={formData.producto_bien_presentado === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>El producto es de buena calidad</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="producto_buena_calidad" value={op.val} checked={formData.producto_buena_calidad === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe información sobre sus compras</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="recibe_informacion" value={op.val} checked={formData.recibe_informacion === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>Recibe información de productos nuevos, variedad y alternativas</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="informacion_productos_nuevos" value={op.val} checked={formData.informacion_productos_nuevos === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                {/* Evaluacion del Personal*/}
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
                                        <input type="radio" name="contacto_con_ejecutivo" value={op.val} checked={formData.contacto_con_ejecutivo === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>La calidad de la atención proporcionada es buena</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="calidad_atencion" value={op.val} checked={formData.calidad_atencion === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                            <tr>
                                <td>El personal tiene dominio de información técnica</td>
                                {opcionesEvaluacion.map((op, i) => (
                                    <td key={i}>
                                        <input type="radio" name="personal_domina_informacion" value={op.val} checked={formData.personal_domina_informacion === op.val} onChange={handleChange} />
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </section>

                {/* Apartado de Redes Sociales*/}
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
                                /> SI
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name="correo_informativo"
                                    value="NO"
                                    checked={formData.correo_informativo === 'NO'}
                                    onChange={handleChange}
                                /> NO
                            </label>
                        </div>
                    </div>
                </section>

                {/*Observaciones y Recomendaciones*/}
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

                <button type="submit" className="btn-submit">
                    Guardar Encuesta y Generar PDF/Excel
                </button>
            </form>
        </main>
    );
    
};

export default RellenarEncuesta;

