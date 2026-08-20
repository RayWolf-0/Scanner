export const validarRut = (rutCompleto) => {
    if (!rutCompleto) return false;
    const cleanRut = rutCompleto.replace(/[^0-9kK]/g, '').toUpperCase();
    if (cleanRut.length < 2) return false;

    const cuerpo = cleanRut.slice(0, -1);
    const dv = cleanRut.slice(-1);

    let suma = 0;
    let multiplo = 2;

    for (let i = 1; i <= cuerpo.length; i++) {
        const index = multiplo * cleanRut.charAt(cuerpo.length - i);
        suma = suma + index;
        multiplo = multiplo < 7 ? multiplo + 1 : 2;
    }

    const dvEsperado = 11 - (suma % 11);
    let dvCalculado = dvEsperado.toString();
    
    if (dvEsperado === 11) dvCalculado = "0";
    if (dvEsperado === 10) dvCalculado = "K";

    return dvCalculado === dv;
};

export const diccionarioCasillas = {
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

    'Casilla 37': { campo: 'red_social_usa', valor: 'Instagram' },
    'Casilla 38': { campo: 'red_social_usa', valor: 'Tiktok' },
    'Casilla 39': { campo: 'red_social_usa', valor: 'Facebook' },
    'Casilla 40': { campo: 'red_social_usa', valor: 'Linkedin' },
    'Casilla 41': { campo: 'red_social_usa', valor: 'Pinterest' },
    'Casilla 42': { campo: 'red_social_usa', valor: 'Ninguna' },

    'Casilla 43': { campo: 'red_social_sigue', valor: 'Instagram' },
    'Casilla 44': { campo: 'red_social_sigue', valor: 'Tiktok' },
    'Casilla 45': { campo: 'red_social_sigue', valor: 'Facebook' },
    'Casilla 47': { campo: 'red_social_sigue', valor: 'Linkedin' },
    'Casilla 48': { campo: 'red_social_sigue', valor: 'Pinterest' },
    'Casilla 49': { campo: 'red_social_sigue', valor: 'Ninguna' },

    'Casilla 50': { campo: 'correo_informativo', valor: 'SI' },
    'Casilla 51': { campo: 'correo_informativo', valor: 'NO' }
};