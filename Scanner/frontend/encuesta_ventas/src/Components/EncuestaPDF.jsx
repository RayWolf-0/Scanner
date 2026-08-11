import React from 'react';
import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

const styles = StyleSheet.create({
  page: { padding: 40, fontFamily: 'Helvetica', fontSize: 9 },
  title: { fontSize: 14, textAlign: 'center', marginBottom: 20, fontFamily: 'Helvetica-Bold' },
  bold: { fontFamily: 'Helvetica-Bold' },

  grid: { borderTop: '1 solid #000', borderLeft: '1 solid #000', marginBottom: 15 },
  row: { flexDirection: 'row' },
  
  clientCell: { width: '50%', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000' },
  clientLabel: { fontSize: 7, color: '#333', marginBottom: 2 },
  clientValue: { fontSize: 9, fontFamily: 'Helvetica-Bold' },

  sectionHeader: { backgroundColor: '#e0e0e0', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000' },
  sectionHeaderText: { fontSize: 10, fontFamily: 'Helvetica-Bold' },

  thQuestion: { width: '60%', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000', justifyContent: 'center', alignItems: 'center' },
  thOption: { width: '10%', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000', justifyContent: 'center', alignItems: 'center' },
  thOptionText: { fontFamily: 'Helvetica-Bold', fontSize: 7, textAlign: 'center' },

  tdQuestion: { width: '60%', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000', justifyContent: 'center' },
  tdOption: { width: '10%', padding: 4, borderRight: '1 solid #000', borderBottom: '1 solid #000', justifyContent: 'center', alignItems: 'center' },

  obsTitle: { fontFamily: 'Helvetica-Bold', fontSize: 10, marginBottom: 5 },
  obsBox: { border: '1 solid #000', minHeight: 60, padding: 6, fontSize: 9 },

  footer: { position: 'absolute', bottom: 30, right: 40, fontSize: 8 },

  redesContainer: { padding: 10, borderRight: '1 solid #000', borderBottom: '1 solid #000' },
  redesRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 15 },
  redesLabel: { width: '40%', fontSize: 9 },
  redesTable: { width: '60%', borderTop: '1 solid #000', borderLeft: '1 solid #000' },
  redesTh: { width: '16.66%', borderRight: '1 solid #000', borderBottom: '1 solid #000', padding: 2, alignItems: 'center' },
  redesTd: { width: '16.66%', borderRight: '1 solid #000', borderBottom: '1 solid #000', height: 16, justifyContent: 'center', alignItems: 'center' },
  
  correoTable: { width: '33.32%', marginLeft: '16.66%', borderTop: '1 solid #000', borderLeft: '1 solid #000' },
  correoTh: { width: '50%', borderRight: '1 solid #000', borderBottom: '1 solid #000', padding: 2, alignItems: 'center' },
  correoTd: { width: '50%', borderRight: '1 solid #000', borderBottom: '1 solid #000', height: 16, justifyContent: 'center', alignItems: 'center' }
});

const FilaEvaluacion = ({ pregunta, respuesta }) => {
  const respVal = String(respuesta || '').toLowerCase();
  return (
    <View style={styles.row}>
      <View style={styles.tdQuestion}><Text>{pregunta}</Text></View>
      <View style={styles.tdOption}><Text style={styles.bold}>{respVal.includes('siempre') ? 'X' : ''}</Text></View>
      <View style={styles.tdOption}><Text style={styles.bold}>{respVal.includes('generalmente') ? 'X' : ''}</Text></View>
      <View style={styles.tdOption}><Text style={styles.bold}>{respVal.includes('rara') ? 'X' : ''}</Text></View>
      <View style={styles.tdOption}><Text style={styles.bold}>{respVal.includes('nunca') ? 'X' : ''}</Text></View>
    </View>
  );
};

const EncuestaPDF = ({ datos = {} }) => {
  const checkRed = (campoArray, campoString, redName) => {
    const valArray = datos[campoArray];
    const valString = datos[campoString];
    const busqueda = redName.toLowerCase();

    if (Array.isArray(valArray)) {
      return valArray.some(item => String(item).toLowerCase().includes(busqueda));
    }
    if (typeof valString === 'string') {
      return valString.toLowerCase().includes(busqueda);
    }
    return false;
  };

  const usaRed = (red) => checkRed('red_social_usa', 'red_mas_usa', red);
  const sigueRed = (red) => checkRed('red_social_sigue', 'red_sigue', red);

  const checkCorreo = (tipo) => {
    const valor = String(datos.correo_informativo || datos.correoInformativo || '').trim().toUpperCase();
    if (tipo === 'SI') return valor === 'SI' || valor === '1' || valor === 'TRUE';
    if (tipo === 'NO') return valor === 'NO' || valor === '0' || valor === 'FALSE';
    return false;
  };

  const redesNombres = ['Instagram', 'Tiktok', 'Facebook', 'LinkedIn', 'Pinterest', 'Ninguna'];

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.title}>ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026</Text>
        
        <View style={styles.grid}>
          <View style={styles.row}>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Nombre Empresa</Text>
              <Text style={styles.clientValue}>{String(datos.empresa || datos.nombre_empresa || ' ')}</Text>
            </View>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>RUT Empresa</Text>
              <Text style={styles.clientValue}>{String(datos.rut || datos.rut_empresa || ' ')}</Text>
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Nombre Encuestado (a)</Text>
              <Text style={styles.clientValue}>{String(datos.encuestado || datos.nombre_encuestado || ' ')}</Text>
            </View>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Cargo</Text>
              <Text style={styles.clientValue}>{String(datos.cargo || ' ')}</Text>
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Correo</Text>
              <Text style={styles.clientValue}>{String(datos.correo || ' ')}</Text>
            </View>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Teléfono</Text>
              <Text style={styles.clientValue}>{String(datos.telefono || ' ')}</Text>
            </View>
          </View>
          <View style={styles.row}>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Fecha</Text>
              <Text style={styles.clientValue}>{String(datos.fecha || ' ')}</Text>
            </View>
            <View style={styles.clientCell}>
              <Text style={styles.clientLabel}>Firma</Text>
              <Text style={styles.clientValue}>{String(datos.firma || ' ')}</Text>
            </View>
          </View>
        </View>

        <View style={styles.grid}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionHeaderText}>1. Evaluación de Servicios Entregados</Text>
          </View>
          <View style={styles.row}>
            <View style={styles.thQuestion}><Text style={styles.bold}>Pregunta</Text></View>
            <View style={styles.thOption}><Text style={styles.thOptionText}>Siempre</Text></View>
            <View style={styles.thOption}><Text style={styles.thOptionText}>General-{"\n"}mente</Text></View>
            <View style={styles.thOption}><Text style={styles.thOptionText}>Rara vez</Text></View>
            <View style={styles.thOption}><Text style={styles.thOptionText}>Nunca</Text></View>
          </View>
          <FilaEvaluacion pregunta="Recibe sus pedidos completos" respuesta={datos.p1_1 || datos.pedidos_completos} />
          <FilaEvaluacion pregunta="Recibe sus pedidos rápidamente (24 - 48 hrs)" respuesta={datos.p1_2 || datos.pedidos_rapidos} />
          <FilaEvaluacion pregunta="Obtiene respuesta oportuna ante reclamos, consultas y requerimientos adicionales" respuesta={datos.p1_3 || datos.respuestas_oportunas} />
        </View>

        <View style={styles.grid}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionHeaderText}>2. Evaluación de Productos Comprados</Text>
          </View>
          <FilaEvaluacion pregunta="El producto está bien presentado (aspecto visual)" respuesta={datos.p2_1 || datos.producto_bien_presentado} />
          <FilaEvaluacion pregunta="El producto es de buena calidad" respuesta={datos.p2_2 || datos.producto_buena_calidad} />
          <FilaEvaluacion pregunta="Recibe información de productos NUEVOS, variedad y alternativas." respuesta={datos.p2_3 || datos.informacion_productos_nuevos} />
        </View>

        <View style={styles.grid}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionHeaderText}>3. Evaluación del Personal</Text>
          </View>
          <FilaEvaluacion pregunta="Recibe contacto permanente de su ejecutivo" respuesta={datos.p3_1 || datos.contacto_con_ejecutivo} />
          <FilaEvaluacion pregunta="La calidad de la atención proporcionada es buena" respuesta={datos.p3_2 || datos.calidad_atencion} />
          <FilaEvaluacion pregunta="El personal tiene dominio de información técnica" respuesta={datos.p3_3 || datos.personal_domina_informacion} />
        </View>

        <View style={styles.grid}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionHeaderText}>4. Redes Sociales <Text style={{ color: 'red' }}>(puede marcar más de una opción)</Text></Text>
          </View>
          <View style={styles.redesContainer}>
            
            <View style={styles.redesRow}>
              <View style={styles.redesLabel}>
                <Text>Qué Red Social es la que más usa</Text>
              </View>
              <View style={styles.redesTable}>
                <View style={styles.row}>
                  {redesNombres.map(red => (
                    <View key={`th1-${red}`} style={styles.redesTh}>
                      <Text style={{ fontSize: 7, fontFamily: 'Helvetica-Bold' }}>{red}</Text>
                    </View>
                  ))}
                </View>
                <View style={styles.row}>
                  {redesNombres.map(red => (
                    <View key={`td1-${red}`} style={styles.redesTd}>
                      <Text style={styles.bold}>{usaRed(red) ? 'X' : ''}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>

            <View style={[styles.redesRow, { alignItems: 'center' }]}>
              <View style={styles.redesLabel}>
                <Text>Cuál es la red Social por donde nos sigue</Text>
              </View>
              <View style={styles.redesTable}>
                <View style={styles.row}>
                  {redesNombres.map(red => (
                    <View key={`td2-${red}`} style={styles.redesTd}>
                      <Text style={styles.bold}>{sigueRed(red) ? 'X' : ''}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>

            <View style={[styles.redesRow, { alignItems: 'center', marginBottom: 0 }]}>
              <View style={styles.redesLabel}>
                <Text>Recibe nuestro correo Informativo</Text>
              </View>
              <View style={styles.correoTable}>
                <View style={styles.row}>
                  <View style={styles.correoTh}><Text style={{ fontSize: 7, fontFamily: 'Helvetica-Bold' }}>SI</Text></View>
                  <View style={styles.correoTh}><Text style={{ fontSize: 7, fontFamily: 'Helvetica-Bold' }}>NO</Text></View>
                </View>
                <View style={styles.row}>
                  <View style={styles.correoTd}><Text style={styles.bold}>{checkCorreo('SI') ? 'X' : ''}</Text></View>
                  <View style={styles.correoTd}><Text style={styles.bold}>{checkCorreo('NO') ? 'X' : ''}</Text></View>
                </View>
              </View>
            </View>

          </View>
        </View>

        <View style={{ marginTop: 5 }}>
          <Text style={styles.obsTitle}>Observaciones y Recomendaciones:</Text>
          <View style={styles.obsBox}>
            <Text>{String(datos.observaciones || datos.obs_recomen || ' ')}</Text>
          </View>
        </View>

        <View style={{ marginTop: 10, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 8, color: '#333' }}>
            Vendedor: <Text style={styles.bold}>{String(datos.usuario || ' ')}</Text>
          </Text>
        </View>

        <Text style={styles.footer}>P-GC-09-REV09</Text>
      </Page>
    </Document>
  );
};

export default EncuestaPDF;