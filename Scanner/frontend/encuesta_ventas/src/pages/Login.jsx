import { useState } from "react";
import { loginRequest } from '../Api/authApi';
import styles from './Login.module.css';

const Login = ({ onLoginSuccess }) => {
    const [usuario, setUsuario] = useState('');
    const [password, setPassword] = useState('');
    const [errormsg, setErrormsg] = useState('');
    const [cargando, setCargando] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrormsg('');
        setCargando(true);

        try {
            const data = await loginRequest(usuario, password);
            localStorage.setItem('usuario_tecbolt', JSON.stringify(data));
            onLoginSuccess(data);
        } catch (error) {
            setErrormsg(error.message);
        } finally {
            setCargando(false);
        }
    };

    return (
        <div className={styles.loginWrapper}>
            <h1 className={styles.loginAppTitle}>Encuestas Tecbolt</h1>
            
            <div className={styles.loginCard}>
                <h2>Login</h2>

                {errormsg && <div className={styles.loginError}>{errormsg}</div>}

                <form onSubmit={handleSubmit}>
                    <div className={styles.loginField}>
                        <label>Usuario</label>
                        <input
                            type="text"
                            value={usuario}
                            onChange={(e) => setUsuario(e.target.value)}
                            required
                        />
                    </div>

                    <div className={styles.loginField}>
                        <label>Contraseña</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button type="submit" className={styles.loginBtn} disabled={cargando}>
                        {cargando ? 'Ingresando...' : 'Ingresar'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;