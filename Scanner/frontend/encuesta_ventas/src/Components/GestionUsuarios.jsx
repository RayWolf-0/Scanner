import React, { useState, useEffect } from 'react';

const GestionUsuarios = ({ onVolver }) => {
  const [usuarios, setUsuarios] = useState([]);
  const [cargando, setCargando] = useState(true);
  
  // formulario
  const [editandoId, setEditandoId] = useState(null);
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [mail, setMail] = useState('');
  const [run, setRun] = useState('');
  const [user, setUser] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [idRol, setIdRol] = useState('1'); // vendedor con rol 1 y supervisor con rol 2
  const [mensaje, setMensaje] = useState('');

  const cargarUsuarios = async () => {
    setCargando(true);
    try {
      const res = await fetch('/api/supervisor/usuarios');
      if (res.ok) {
        const data = await res.json();
        setUsuarios(data.usuarios || []);
      }
    } catch (error) {
      console.error('Error al cargar usuarios:', error);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarUsuarios();
  }, []);

  const limpiarFormulario = () => {
    setEditandoId(null);
    setNombre('');
    setApellido('');
    setMail('');
    setRun('');
    setUser('');
    setContrasena('');
    setIdRol('1');
  };

  const iniciarEdicion = (u) => {
    setEditandoId(u.id_usuario);
    setNombre(u.nombre);
    setApellido(u.apellido);
    setMail(u.mail);
    setRun(u.run);
    setUser(u.user);
    setContrasena(''); 
    setIdRol(String(u.id_rol));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje('');

    const url = editandoId 
      ? `/api/supervisor/usuarios/actualizar/${editandoId}`
      : '/api/supervisor/usuarios/crear';
      
    const metodo = editandoId ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method: metodo,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre,
          apellido,
          mail,
          run,
          user,
          contrasena,
          id_rol: Number(idRol)
        })
      });

      const data = await res.json();
      if (res.ok) {
        setMensaje(editandoId ? '¡Usuario actualizado con éxito!' : '¡Usuario creado con éxito!');
        limpiarFormulario();
        cargarUsuarios();
      } else {
        setMensaje('Error: ' + (data.error || data.detail || data.mensaje));
      }
    } catch (error) {
      console.error(error);
      setMensaje('Error de conexión con el servidor');
    }
  };

  const eliminarUsuario = async (id) => {
    if (!window.confirm("¿Estás seguro de que deseas eliminar este usuario? Esta acción no se puede deshacer.")) {
      return;
    }
    setMensaje('');
    try {
      const res = await fetch(`/api/supervisor/usuarios/eliminar/${id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (res.ok) {
        setMensaje('¡Usuario eliminado con éxito!');
        cargarUsuarios();
      } else {
        setMensaje('Error: ' + (data.error || data.detail || data.mensaje));
      }
    } catch (error) {
      console.error(error);
      setMensaje('Error de conexión con el servidor');
    }
  };

  return (
    <div className="historial-container" style={{ padding: '20px' }}>
      <div className="historial-card" style={{ maxWidth: '980px', margin: 'auto' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 className="historial-title" style={{ margin: 0 }}>Gestión de Vendedores y Supervisores</h2>
          <button className="btn-accion" onClick={onVolver} style={{ background: '#6c757d', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>
            ← Volver al Perfil
          </button>
        </div>

        {/* Crear y editar usuarios */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '20px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', marginBottom: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', color: '#fff' }}>
              {editandoId ? `Editando Usuario (ID: ${editandoId})` : 'Crear Nuevo Usuario'}
            </h3>
            {editandoId && (
              <button onClick={limpiarFormulario} style={{ background: '#dc3545', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
                Cancelar Edición
              </button>
            )}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>Nombre:</label>
              <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} required style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>Apellido:</label>
              <input type="text" value={apellido} onChange={(e) => setApellido(e.target.value)} required style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>Correo Electrónico (Mail):</label>
              <input type="email" value={mail} onChange={(e) => setMail(e.target.value)} required style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>RUN:</label>
              <input type="text" value={run} onChange={(e) => setRun(e.target.value)} required placeholder="Ej: 12345678-9" style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>Nombre de Usuario (User):</label>
              <input type="text" value={user} onChange={(e) => setUser(e.target.value)} required style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>
                {editandoId ? 'Nueva Contraseña (Opcional):' : 'Contraseña Inicial:'}
              </label>
              <input type="password" value={contrasena} onChange={(e) => setContrasena(e.target.value)} placeholder={editandoId ? 'Dejar en blanco para no cambiar' : ''} required={!editandoId} style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#ccc', display: 'block', marginBottom: '4px' }}>Rol Asignado:</label>
              <select value={idRol} onChange={(e) => setIdRol(e.target.value)} style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}>
                <option value="1">Vendedor</option>
                <option value="2">Supervisor</option>
              </select>
            </div>
            <div style={{ gridColumn: 'span 2', marginTop: '10px' }}>
              <button type="submit" className="btn-accion btn-excel" style={{ width: '100%', background: editandoId ? '#ffc107' : '#28a745', color: editandoId ? '#000' : '#fff', borderColor: 'transparent', padding: '10px', fontWeight: 'bold', cursor: 'pointer' }}>
                {editandoId ? 'Guardar Cambios' : 'Registrar Nuevo Usuario'}
              </button>
            </div>
          </form>
          {mensaje && <p style={{ marginTop: '10px', fontSize: '13px', color: mensaje.includes('éxito') || mensaje.includes('correctamente') ? '#51cf66' : '#ff6b6b' }}>{mensaje}</p>}
        </div>

        {/* Lista los usuarios */}
        <h3 style={{ fontSize: '16px', color: '#fff', marginBottom: '10px' }}>Usuarios Registrados en el Sistema</h3>
        {cargando ? (
          <p className="status-msg">Cargando usuarios...</p>
        ) : (
          <div className="tabla-responsive">
            <table className="tabla-historial">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nombre Completo</th>
                  <th>Usuario</th>
                  <th>Correo</th>
                  <th>RUN</th>
                  <th>Rol</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u) => (
                  <tr key={u.id_usuario}>
                    <td>{u.id_usuario}</td>
                    <td>{u.nombre} {u.apellido}</td>
                    <td>{u.user}</td>
                    <td>{u.mail}</td>
                    <td>{u.run}</td>
                    <td>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', background: u.id_rol === 2 ? '#007bff' : '#6c757d', color: '#fff', fontSize: '12px' }}>
                        {u.rol}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button 
                          onClick={() => iniciarEdicion(u)} 
                          style={{ background: '#17a2b8', color: '#fff', border: 'none', padding: '5px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                        >
                          Editar
                        </button>
                        <button 
                          onClick={() => eliminarUsuario(u.id_usuario)} 
                          style={{ background: '#dc3545', color: '#fff', border: 'none', padding: '5px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
};

export default GestionUsuarios;