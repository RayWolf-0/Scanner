import React, { useState, useRef } from "react";
import { guardarEncuesta } from "../Api/encuestaApi";
import * as XLSX from 'xlsx';
import { PDFDownloadLink } from '@react-pdf/renderer';
import EncuestaPDF from '../Components/EncuestaPDF'; 

const RellenarEncuesta = ({ onGuardadoExitoso }) => {
    const fileInputRef = useRef(null);
    const [isScanning, setIsScanning] = useState(false);
    const [progreso, setProgreso] = useState(0); // Estado para la barra de progreso

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

    // funcion para bajarle el peso a la imagen usando canvas
    const comprimirImagen = (file) => {
        return new Promise((resolve) => {
            const reader = new FileReader(); 
            reader.readAsDataURL(file);
            reader.onload = (event) => {
                const img = new Image();
                img.src = event.target.result;
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const MAX_WIDTH = 1200;
                    const MAX_HEIGHT = 1200;
                    let width = img.width;
                    let height = img.height;

                    if (width > height) {
                        if (width > MAX_WIDTH) {
                            height *= MAX_WIDTH / width;
                            width = MAX_WIDTH;
                        }
                    } else {
                        if (height > MAX_HEIGHT) {
                            width *= MAX_HEIGHT / height;
                            height = MAX_HEIGHT;
                        }
                    }

                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // comprimir a jpeg al 70% de calidad
                    canvas.toBlob((blob) => {
                        resolve(new File([blob], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        }));
                    }, 'image/jpeg', 0.7);
                };
            };
        });
    };

    // funcion del scanner
    const handleFileChange = async (e) => {
        const fileOriginal = e.target.files[0];
        if (!fileOriginal) return;

        setIsScanning(true);
        setProgreso(10);

        // Simulador de barra de progreso fluida
        const intervalo = setInterval(() => {
            setProgreso((prev) => (prev >= 85 ? 85 : prev + 15));
        }, 600);
        
        try {
            const fileComprimido = await comprimirImagen(fileOriginal);
            const scanData = new FormData();
            scanData.append("imagen", fileComprimido);

            const response = await fetch("http://192.168.17.72:8082/api/scanner/analizar", {
                method: "POST",
                body: scanData,
            });
            
            if (!response.ok) {
                throw new Error(`Error de red o servidor: ${response.status}`);
            }

            const result = await response.json();

            clearInterval(intervalo);
            setProgreso(100);

            if (result.status === 'success' && result.data) {
                const apiData = result.data;
                
                setFormData((prev) => {
                    const newData = { ...prev };
                    
                    // 1. Mapear datos de texto y LIMPIEZA
                    if (apiData.nombre_empresa) newData.nombre_empresa = apiData.nombre_empresa.trim();
                    if (apiData.nombre_encuestado) newData.nombre_encuestado = apiData.nombre_encuestado.trim();
                    if (apiData.cargo) newData.cargo = apiData.cargo.trim();
                    if (apiData.fecha) {
                        let fCruda = apiData.fecha.replace(/\s+/g, '').replace(/\//g, '-');
                        let partes = fCruda.split('-');
                        if (partes.length === 3 && partes[0].length <= 2) {
                            newData.fecha = `${partes[2]}-${partes[1].padStart(2, '0')}-${partes[0].padStart(2, '0')}`;
                        } else {
                            newData.fecha = fCruda;
                        }
                    }
                    if (apiData.telefono) newData.telefono = apiData.telefono.replace(/\D/g, ''); // Solo números
                    
                    // correo
                    if (apiData.correo) newData.correo = apiData.correo.replace(/\s+/g, '');
                    if (apiData.observaciones) newData.obs_recomen = apiData.observaciones.trim();

                    // rut, agrega el guión automático
                    if (apiData.rut_empresa) {
                        let rutCrudo = apiData.rut_empresa.replace(/[^0-9Kk]/g, '').toUpperCase();
                        if (rutCrudo.length >= 8 && !rutCrudo.includes('-')) {
                            newData.rut_empresa = rutCrudo.slice(0, -1) + '-' + rutCrudo.slice(-1);
                        } else {
                            newData.rut_empresa = rutCrudo;
                        }
                    }

                    // Traductor exacto de casillas
                    const diccionarioCasillas = {
                    // 1. Evaluación de Servicios Entregados
                        'Casilla 1': { campo: 'pedidos_completos', valor: 'Siempre >90%' },
                        'Casilla 2': { campo: 'pedidos_completos', valor: 'Generalmente 65%-89%' },
                        'Casilla 3': { campo: 'pedidos_completos', valor: 'Rara vez 40%-64%' },
                        'Casilla 4': { campo: 'pedidos_completos', valor: 'Nunca <40%' },

                        'Casilla 5': { campo: 'pedidos_rapidos', valor: 'Siempre >90%' },
                        'Casilla 6': { campo: 'pedidos_rapidos', valor: 'Generalmente 65%-89%' },
                        'Casilla 7': { campo: 'pedidos_rapidos', valor: 'Rara vez 40%-64%' },
                        'Casilla 8': { campo: 'pedidos_rapidos', valor: 'Nunca <40%' },

                        'Casilla 9': { campo: 'respuestas_oportunas', valor: 'Siempre >90%' },
                        'Casilla 10': { campo: 'respuestas_oportunas', valor: 'Generalmente 65%-89%' },
                        'Casilla 11': { campo: 'respuestas_oportunas', valor: 'Rara vez 40%-64%' },
                        'Casilla 12': { campo: 'respuestas_oportunas', valor: 'Nunca <40%' },

                    // 2. Evaluación de Productos Comprados
                        'Casilla 13': { campo: 'producto_bien_presentado', valor: 'Siempre >90%' },
                        'Casilla 14': { campo: 'producto_bien_presentado', valor: 'Generalmente 65%-89%' },
                        'Casilla 15': { campo: 'producto_bien_presentado', valor: 'Rara vez 40%-64%' },
                        'Casilla 16': { campo: 'producto_bien_presentado', valor: 'Nunca <40%' },

                        'Casilla 17': { campo: 'producto_buena_calidad', valor: 'Siempre >90%' },
                        'Casilla 18': { campo: 'producto_buena_calidad', valor: 'Generalmente 65%-89%' },
                        'Casilla 19': { campo: 'producto_buena_calidad', valor: 'Rara vez 40%-64%' },
                        'Casilla 20': { campo: 'producto_buena_calidad', valor: 'Nunca <40%' },

                        'Casilla 21': { campo: 'informacion_productos_nuevos', valor: 'Siempre >90%' },
                        'Casilla 22': { campo: 'informacion_productos_nuevos', valor: 'Generalmente 65%-89%' },
                        'Casilla 23': { campo: 'informacion_productos_nuevos', valor: 'Rara vez 40%-64%' },
                        'Casilla 24': { campo: 'informacion_productos_nuevos', valor: 'Nunca <40%' },

                    // 3. Evaluación del Personal
                        'Casilla 25': { campo: 'contacto_con_ejecutivo', valor: 'Siempre >90%' },
                        'Casilla 26': { campo: 'contacto_con_ejecutivo', valor: 'Generalmente 65%-89%' },
                        'Casilla 27': { campo: 'contacto_con_ejecutivo', valor: 'Rara vez 40%-64%' },
                        'Casilla 28': { campo: 'contacto_con_ejecutivo', valor: 'Nunca <40%' },

                        'Casilla 29': { campo: 'calidad_atencion', valor: 'Siempre >90%' },
                        'Casilla 30': { campo: 'calidad_atencion', valor: 'Generalmente 65%-89%' },
                        'Casilla 31': { campo: 'calidad_atencion', valor: 'Rara vez 40%-64%' },
                        'Casilla 32': { campo: 'calidad_atencion', valor: 'Nunca <40%' },

                        'Casilla 33': { campo: 'personal_domina_informacion', valor: 'Siempre >90%' },
                        'Casilla 34': { campo: 'personal_domina_informacion', valor: 'Generalmente 65%-89%' },
                        'Casilla 35': { campo: 'personal_domina_informacion', valor: 'Rara vez 40%-64%' },
                        'Casilla 36': { campo: 'personal_domina_informacion', valor: 'Nunca <40%' },

                    // 4. Redes Sociales (¿Qué red social usa más?)
                        'Casilla 37': { campo: 'red_social_usa', valor: 'Instagram' },
                        'Casilla 38': { campo: 'red_social_usa', valor: 'Tiktok' },
                        'Casilla 39': { campo: 'red_social_usa', valor: 'Facebook' },
                        'Casilla 40': { campo: 'red_social_usa', valor: 'Linkedin' },
                        'Casilla 41': { campo: 'red_social_usa', valor: 'Pinterest' },
                        'Casilla 42': { campo: 'red_social_usa', valor: 'Ninguna' },

                    // ¿Por dónde nos sigue? 
                        'Casilla 43': { campo: 'red_social_sigue', valor: 'Instagram' },
                        'Casilla 44': { campo: 'red_social_sigue', valor: 'Tiktok' },
                        'Casilla 45': { campo: 'red_social_sigue', valor: 'Facebook' },
                        'Casilla 47': { campo: 'red_social_sigue', valor: 'Linkedin' },
                        'Casilla 48': { campo: 'red_social_sigue', valor: 'Pinterest' },
                        'Casilla 49': { campo: 'red_social_sigue', valor: 'Ninguna' },

                    // Correo Informativo
                        'Casilla 50': { campo: 'correo_informativo', valor: 'SI' },
                        'Casilla 51': { campo: 'correo_informativo', valor: 'NO' }
                    };


                    // Limpiar arrays para que no se dupliquen
                    newData.red_social_usa = [];
                    newData.red_social_sigue = [];

                    // Recorrer el resultado del backend
                    Object.keys(apiData).forEach(key => {
                        if (key.startsWith('Casilla') && apiData[key] === true) {
                            const traduccion = diccionarioCasillas[key];
                            if (traduccion) {
                                if (traduccion.campo === 'red_social_usa' || traduccion.campo === 'red_social_sigue') {
                                    if (!newData[traduccion.campo].includes(traduccion.valor)) {
                                        newData[traduccion.campo].push(traduccion.valor);
                                    }
                                } else {
                                    newData[traduccion.campo] = traduccion.valor;
                                }
                            }
                        }
                    });

                    return newData;
                });
                
                setTimeout(() => {
                    alert("¡Planilla escaneada con éxito! Por favor revisa los datos antes de guardar.");
                    setProgreso(0);
                    setIsScanning(false);
                }, 500);

            } else {
                alert("Error al escanear: " + (result.error || result.mensaje));
                setProgreso(0);
                setIsScanning(false);
            }
        } catch (error) {
            clearInterval(intervalo);
            setProgreso(0);
            setIsScanning(false);
            console.error("Error de conexión con el escáner:", error);
            alert("Ocurrió un error al intentar comunicarse con el motor inteligente.");
        } finally {
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    // funcion para validar RUT
    const validarRut = (rutCompleto) => {
        if (!rutCompleto) return false;
        // acepta numeros y k
        const cleanRut = rutCompleto.replace(/[^0-9kK]/g, '').toUpperCase();
        if (cleanRut.length < 2) return false;

        const cuerpo = cleanRut.slice(0, -1);
        const dv = cleanRut.slice(-1);

        let suma = 0;
        let multiplo = 2;

        // calculo del rut
        for (let i = 1; i <= cuerpo.length; i++) {
            const index = multiplo * cleanRut.charAt(cuerpo.length - i);
            suma = suma + index;
            if (multiplo < 7) { 
                multiplo = multiplo + 1; 
            } else { 
                multiplo = 2; 
            }
        }

        const dvEsperado = 11 - (suma % 11);
        let dvCalculado = dvEsperado.toString();
        
        if (dvEsperado === 11) dvCalculado = "0";
        if (dvEsperado === 10) dvCalculado = "K";

        return dvCalculado === dv;
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

            // filtros estrictos de caracteres
            if (name === 'rut_empresa') {
                valorProcesado = value.replace(/[.,]/g, '');
            }
            else if (name === 'telefono') {
                valorProcesado = value.replace(/\D/g, '');
            }
            else if (name === 'nombre_empresa' || name === 'nombre_encuestado') {
                valorProcesado = value.replace(/[0-9.,]/g, '');
            }
            else if (name === 'cargo') {
                valorProcesado = value.replace(/[.,]/g, '');
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

        // verificar el RUT antes de intentar guardarlo
        if (!validarRut(formData.rut_empresa)) {
            alert('El RUT ingresado no es válido. Por favor, verifíquelo antes de guardar.');
            return; // detiene el envío si el RUT está mal
        }

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

                {/* apartado del scanner */}
                <section className="form-section" style={{ backgroundColor: '#eef2f7', border: '2px dashed #007bff', textAlign: 'center', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                    <h3>Escáner de Planillas</h3>
                    <p style={{ fontSize: '14px', color: '#555', marginBottom: '15px' }}>
                        Sube una fotografía de la encuesta física y la Inteligencia Artificial llenará los datos por ti.
                    </p>
                    <input 
                        type="file" 
                        accept="image/*" 
                        capture="environment" // habilita la camara en moviles
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        onChange={handleFileChange}
                    />
                    <button 
                        type="button" 
                        onClick={() => fileInputRef.current.click()} 
                        disabled={isScanning}
                        style={{ 
                            padding: '12px 24px', 
                            fontSize: '15px', 
                            fontWeight: 'bold',
                            borderRadius: '6px', 
                            cursor: isScanning ? 'not-allowed' : 'pointer', 
                            backgroundColor: isScanning ? '#6c757d' : '#007bff', 
                            color: 'white', 
                            border: 'none',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                        }}
                    >
                        {isScanning ? 'Analizando imagen con IA...' : 'Tomar Foto o Subir Archivo'}
                    </button>

                    {/* BARRA DE PROGRESO */}
                    {isScanning && (
                        <div className="progress-container" style={{ marginTop: '15px', width: '100%', backgroundColor: '#cbd5e0', borderRadius: '8px', overflow: 'hidden', height: '22px', position: 'relative' }}>
                            <div className="progress-bar" style={{ width: `${progreso}%`, height: '100%', background: 'linear-gradient(90deg, #3182ce, #63b3ed)', transition: 'width 0.4s ease' }}></div>
                            <span style={{ position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)', fontSize: '0.85rem', fontWeight: 'bold', color: '#1a202c', lineHeight: '22px' }}>{progreso}% Procesando</span>
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
                                        <span style={{ color: '#28a745', fontSize: '13px', fontWeight: 'bold' }}>🟢</span>
                                    ) : (
                                        <span style={{ color: '#dc3545', fontSize: '13px', fontWeight: 'bold' }}>🔴 RUT incorrecto</span>
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

                {/* botones de acción */}
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