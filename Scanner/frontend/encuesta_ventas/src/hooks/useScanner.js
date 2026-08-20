import { useState } from "react";
import { diccionarioCasillas } from "../utils/surveyUtils";

export const useScanner = () => {
    const [isScanning, setIsScanning] = useState(false);
    const [progreso, setProgreso] = useState(0);

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
                        if (width > MAX_WIDTH) { height *= MAX_WIDTH / width; width = MAX_WIDTH; }
                    } else {
                        if (height > MAX_HEIGHT) { width *= MAX_HEIGHT / height; height = MAX_HEIGHT; }
                    }

                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob((blob) => {
                        resolve(new File([blob], file.name, { type: 'image/jpeg', lastModified: Date.now() }));
                    }, 'image/jpeg', 0.7);
                };
            };
        });
    };

    const procesarImagenEscaneada = async (fileOriginal) => {
        if (!fileOriginal) return null;
        setIsScanning(true);
        setProgreso(10);

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
            
            if (!response.ok) throw new Error(`Error de servidor: ${response.status}`);

            const result = await response.json();
            clearInterval(intervalo);
            setProgreso(100);

            if (result.status === 'success' && result.data) {
                const apiData = result.data;
                const newData = {
                    nombre_empresa: apiData.nombre_empresa?.trim() || '',
                    nombre_encuestado: apiData.nombre_encuestado?.trim() || '',
                    cargo: apiData.cargo?.trim() || '',
                    telefono: apiData.telefono?.replace(/\D/g, '') || '',
                    correo: apiData.correo?.replace(/\s+/g, '') || '',
                    obs_recomen: apiData.observaciones?.trim() || '',
                    red_social_usa: [],
                    red_social_sigue: []
                };

                if (apiData.fecha) {
                    let fCruda = apiData.fecha.replace(/\s+/g, '').replace(/\//g, '-');
                    let partes = fCruda.split('-');
                    newData.fecha = (partes.length === 3 && partes[0].length <= 2) 
                        ? `${partes[2]}-${partes[1].padStart(2, '0')}-${partes[0].padStart(2, '0')}` 
                        : fCruda;
                }

                if (apiData.rut_empresa) {
                    let rutCrudo = apiData.rut_empresa.replace(/[^0-9Kk]/g, '').toUpperCase();
                    newData.rut_empresa = (rutCrudo.length >= 8 && !rutCrudo.includes('-')) 
                        ? rutCrudo.slice(0, -1) + '-' + rutCrudo.slice(-1) 
                        : rutCrudo;
                }

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

                setTimeout(() => {
                    setIsScanning(false);
                    setProgreso(0);
                }, 500);

                return newData;
            }
        } catch (error) {
            clearInterval(intervalo);
            setProgreso(0);
            setIsScanning(false);
            console.error("Error en escáner:", error);
            alert("Error al intentar comunicarse con el motor inteligente.");
            return null;
        }
    };

    return { procesarImagenEscaneada, isScanning, progreso };
};