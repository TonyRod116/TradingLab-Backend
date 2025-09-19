// Script para debuggear el problema del perfil en el frontend
console.log('🔍 Debug Frontend Profile');

// Verificar si hay token en localStorage
const token = localStorage.getItem('token');
console.log('🔍 Token en localStorage:', token ? 'Presente' : 'Ausente');

// Verificar si hay usuario en localStorage
const user = localStorage.getItem('user');
console.log('🔍 Usuario en localStorage:', user ? JSON.parse(user) : 'Ausente');

// Verificar si hay token en sessionStorage
const sessionToken = sessionStorage.getItem('token');
console.log('🔍 Token en sessionStorage:', sessionToken ? 'Presente' : 'Ausente');

// Verificar si hay usuario en sessionStorage
const sessionUser = sessionStorage.getItem('user');
console.log('🔍 Usuario en sessionStorage:', sessionUser ? JSON.parse(sessionUser) : 'Ausente');

// Verificar si hay token en cookies
const cookies = document.cookie;
console.log('🔍 Cookies:', cookies);

// Verificar si hay algún error en la consola
console.log('🔍 Verificar si hay errores en la consola del navegador');

// Función para probar la petición al perfil
async function testProfileRequest() {
    try {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        if (!token) {
            console.error('❌ No hay token disponible');
            return;
        }
        
        console.log('🔍 Probando petición al perfil...');
        const response = await fetch('http://localhost:8000/api/users/profile/', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🔍 Status:', response.status);
        console.log('🔍 Headers:', response.headers);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Datos del perfil:', data);
        } else {
            const errorText = await response.text();
            console.error('❌ Error:', response.status, errorText);
        }
    } catch (error) {
        console.error('❌ Error en la petición:', error);
    }
}

// Ejecutar test
testProfileRequest();






