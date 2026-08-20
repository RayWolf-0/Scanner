import * as XLSX from 'xlsx';

export const generarExcelAutomatizado = async (encuestasFiltradas, vendedorFiltro, API_BASE_URL, getVendedorNombre, setExportando) => {
    if (encuestasFiltradas.length === 0) {
        alert("No hay encuestas para exportar.");
        return;
    }
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