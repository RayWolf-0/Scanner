export const loginRequest = async (usuario, password) => {
    try{
        const response = await fetch('/api/auth/login' ,{
            method: 'POST',
            headers: {'Content-Type': 'application/json' },
            body: JSON.stringify({usuario, password})
        });
        const data = await response.json();
        if (!response.ok){
            throw new Error(data.error || 'Error al iniciar sesión');    
        }

        return data;

    }catch(error){
        throw error;
    }
};