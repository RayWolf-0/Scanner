const API_URL = '';

export const guardarEncuesta = async (datos) => {
    try {
        const response = await fetch(`${API_URL}/api/encuesta/guardar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Error al guardar la encuesta');
        }
        return data;
    } catch (error) {
        console.error("Error de Conexión", error);
        throw error;
    }
};