import React from 'react';
import styles from './EditarEncuestaModal.module.css';

const REDES_OPCIONES = ['Instagram', 'TikTok', 'Facebook', 'LinkedIn', 'Pinterest', 'Ninguna'];

const EditarEncuestaModal = ({ encuestaEditando, setEncuestaEditando, handleGuardarEdicion, onCerrar }) => {
    if (!encuestaEditando) return null;

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

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalContent}>
                <h3>Editar Encuesta Completa</h3>
                <form onSubmit={handleGuardarEdicion}>
                    <h4>Datos de la Empresa / Cliente</h4>
                    <div className={styles.formGroupModal}>
                        <label>Nombre Empresa:</label>
                        <input type="text" value={encuestaEditando.empresa || encuestaEditando.nombre_empresa || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, empresa: e.target.value, nombre_empresa: e.target.value })} required />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>RUT Empresa:</label>
                        <input type="text" value={encuestaEditando.rut || encuestaEditando.rut_empresa || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, rut: e.target.value, rut_empresa: e.target.value })} />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>Encuestado(a):</label>
                        <input type="text" value={encuestaEditando.encuestado || encuestaEditando.nombre_encuestado || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, encuestado: e.target.value, nombre_encuestado: e.target.value })} required />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>Cargo:</label>
                        <input type="text" value={encuestaEditando.cargo || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, cargo: e.target.value })} />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>Correo:</label>
                        <input type="email" value={encuestaEditando.correo || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo: e.target.value })} />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>Teléfono:</label>
                        <input type="text" value={encuestaEditando.telefono || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, telefono: e.target.value })} />
                    </div>
                    <div className={styles.formGroupModal}>
                        <label>Fecha:</label>
                        <input type="date" value={encuestaEditando.fecha || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, fecha: e.target.value })} required />
                    </div>

                    <h4 style={{ marginTop: '15px' }}>1. Evaluación de Servicios</h4>
                    {['p1_1', 'p1_2', 'p1_3'].map((p, idx) => (
                        <div className={styles.formGroupModal} key={p}>
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
                        <div className={styles.formGroupModal} key={p}>
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
                        <div className={styles.formGroupModal} key={p}>
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
                    <div className={styles.formGroupModal}>
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

                    <div className={styles.formGroupModal} style={{ marginTop: '12px' }}>
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

                    <div className={styles.formGroupModal} style={{ marginTop: '12px' }}>
                        <label>Recibe nuestro correo Informativo:</label>
                        <select value={String(encuestaEditando.correo_informativo) === '1' || String(encuestaEditando.correo_informativo).toUpperCase() === 'SI' || String(encuestaEditando.correo_informativo).toUpperCase() === 'TRUE' ? '1' : '0'} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, correo_informativo: Number(e.target.value) })}>
                            <option value="1">SI</option>
                            <option value="0">NO</option>
                        </select>
                    </div>

                    <div className={styles.formGroupModal} style={{ marginTop: '12px' }}>
                        <label>Observaciones y Recomendaciones:</label>
                        <textarea rows="3" style={{ width: '100%', padding: '8px', marginTop: '4px' }} value={encuestaEditando.observaciones || encuestaEditando.obs_recomen || ''} onChange={(e) => setEncuestaEditando({ ...encuestaEditando, observaciones: e.target.value, obs_recomen: e.target.value })} />
                    </div>

                    <div className={styles.modalActions} style={{ marginTop: '20px' }}>
                        <button type="button" className={styles.btnCancelar} onClick={onCerrar}>Cancelar</button>
                        <button type="submit" className={styles.btnGuardarModal}>Guardar Todos los Cambios</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditarEncuestaModal;