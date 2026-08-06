export const guardarEncuesta = async (datos) => {
    try{
        const response = await fetch('/api/encuesta/guardar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(datos)
        });
        return await response.json();
    }catch(error){
        console.error("Error de Conexión", error);
        throw error;
    }
};