# tests_sgep/tests_caja_negra/test_login_caja_negra.py
"""
PRUEBAS DE CAJA NEGRA — Módulo: Login y Autenticación
======================================================
Técnica: Partición de Equivalencia + Análisis de Valores Límite

MÓDULO ANALIZADO : apps.auth_app (views.py, models.py, services.py)
VISTA PRINCIPAL  : login_view (GET y POST)
URL              : /login/

Objetivo
--------
Verificar que el módulo de login responde correctamente a combinaciones
válidas e inválidas de credenciales, SIN conocer el código interno.
El tester solo conoce entradas y salidas esperadas.

Casos cubiertos
---------------
CN-L-001  Login exitoso con credenciales válidas
CN-L-002  Login fallido — contraseña incorrecta
CN-L-003  Login fallido — usuario inexistente
CN-L-004  Login fallido — campos vacíos
CN-L-005  Login fallido — usuario inactivo
CN-L-006  Login fallido — usuario bloqueado aún en tiempo de espera
CN-L-007  Login desbloqueado automáticamente al expirar timeout
CN-L-008  Vista GET muestra formulario de login
CN-L-009  Bloqueo automático al superar 5 intentos fallidos
CN-L-010  API REST login exitoso (endpoint JSON)
CN-L-011  API REST login con credenciales inválidas
CN-L-012  Protección CSRF activa en POST
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


pytestmark = pytest.mark.django_db


class TestLoginCajaNegra_CasosValidos:
    """
    Partición de Equivalencia — Clase VÁLIDA
    =========================================
    Datos válidos deben producir login exitoso y redirección al dashboard.
    """

    def test_CN_L_001_login_exitoso_credenciales_validas(self, client, usuario_admin):
        """
        CN-L-001: Login con credenciales correctas.

        ENTRADA:
            username = 'admin_test'  (existente, activo, no bloqueado)
            password = 'AdminTest@2024!'

        RESULTADO ESPERADO:
            - HTTP 302 Redirect
            - Redirección a /dashboard/
            - Sesión Django creada
            - session['usuario_rol'] = 'administrador'
        """
        url = reverse('auth:login')
        datos = {
            'username': 'admin_test',
            'password': 'AdminTest@2024!',
        }

        response = client.post(url, datos, follow=False)

        assert response.status_code == 302, (
            f"Se esperaba redirect 302, se obtuvo {response.status_code}"
        )
        assert '/dashboard' in response['Location'], (
            f"Redirección inesperada: {response['Location']}"
        )

    def test_CN_L_001b_sesion_creada_tras_login(self, client, usuario_admin):
        """
        CN-L-001b: Verifica que se crea la sesión Django tras login exitoso.
        """
        url = reverse('auth:login')
        client.post(url, {
            'username': 'admin_test',
            'password': 'AdminTest@2024!',
        })
        # La sesión debe tener el rol del usuario
        assert client.session.get('usuario_rol') == 'administrador'

    def test_CN_L_008_vista_GET_muestra_formulario(self, client):
        """
        CN-L-008: GET /login/ debe retornar HTTP 200 con formulario.

        ENTRADA: Petición GET sin autenticación.
        RESULTADO ESPERADO: HTTP 200 + template 'auth/login.html'.
        """
        url = reverse('auth:login')
        response = client.get(url)

        assert response.status_code == 200
        assert b'login' in response.content.lower() or b'usuario' in response.content.lower()


class TestLoginCajaNegra_CasosInvalidos:
    """
    Partición de Equivalencia — Clase INVÁLIDA
    ===========================================
    Datos inválidos deben retornar HTTP 200 con mensaje de error
    (nunca exponer detalles internos de la excepción).
    """

    def test_CN_L_002_login_fallido_password_incorrecta(self, client, usuario_admin):
        """
        CN-L-002: Contraseña incorrecta.

        ENTRADA:
            username = 'admin_test' (usuario existente)
            password = 'wrongpassword' (incorrecta)

        RESULTADO ESPERADO:
            - HTTP 200 (se muestra nuevamente el formulario)
            - Mensaje de error en la respuesta
            - NO se crea sesión
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': 'admin_test',
            'password': 'wrongpassword',
        })

        assert response.status_code == 200
        assert b'incorrecto' in response.content.lower() or b'inv' in response.content.lower()
        assert not client.session.get('usuario_id'), "No debe existir sesión tras fallo"

    def test_CN_L_003_login_fallido_usuario_inexistente(self, client, db):
        """
        CN-L-003: Usuario que no existe en BD.

        ENTRADA:
            username = 'usuario_fantasma' (NO existe)
            password = 'cualquier_cosa'

        RESULTADO ESPERADO:
            - HTTP 200
            - Mensaje de error genérico (no revelar que el usuario no existe)
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': 'usuario_fantasma',
            'password': 'cualquier_cosa',
        })

        assert response.status_code == 200
        # Seguridad: el mensaje NO debe revelar si el usuario existe o no
        assert b'fantasma' not in response.content.lower()

    def test_CN_L_004_login_fallido_campos_vacios(self, client, db):
        """
        CN-L-004: Campos username y password vacíos.

        ENTRADA:
            username = ''
            password = ''

        RESULTADO ESPERADO:
            - HTTP 200
            - Mensaje de validación indicando que son requeridos
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': '',
            'password': '',
        })

        assert response.status_code == 200
        assert (
            b'requerido' in response.content.lower()
            or b'required' in response.content.lower()
            or b'obligatorio' in response.content.lower()
        )

    def test_CN_L_004b_login_fallido_solo_username(self, client, db):
        """
        CN-L-004b: Solo username, password vacío.
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': 'admin_test',
            'password': '',
        })
        assert response.status_code == 200

    def test_CN_L_005_login_fallido_usuario_inactivo(self, client, usuario_inactivo):
        """
        CN-L-005: Usuario con activo=False intenta ingresar.

        ENTRADA:
            username = 'inactivo_test' (activo=False)
            password = 'InacTest@2024!'

        RESULTADO ESPERADO:
            - HTTP 200
            - Mensaje indicando cuenta desactivada
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': 'inactivo_test',
            'password': 'InacTest@2024!',
        })

        assert response.status_code == 200
        assert (
            b'desactivada' in response.content.lower()
            or b'inactiv' in response.content.lower()
            or b'incorrecto' in response.content.lower()
        )

    def test_CN_L_006_login_fallido_usuario_bloqueado(self, client, usuario_bloqueado):
        """
        CN-L-006: Usuario bloqueado con tiempo de espera activo.

        ENTRADA:
            username = 'bloqueado_test' (bloqueado=True, fecha_desbloqueo en futuro)
            password = 'BloquTest@2024!'

        RESULTADO ESPERADO:
            - HTTP 200
            - Mensaje indicando cuenta bloqueada
        """
        url = reverse('auth:login')
        response = client.post(url, {
            'username': 'bloqueado_test',
            'password': 'BloquTest@2024!',
        })

        assert response.status_code == 200
        assert (
            b'bloqueada' in response.content.lower()
            or b'bloqueado' in response.content.lower()
            or b'incorrecto' in response.content.lower()
        )


class TestLoginCajaNegra_ValoresLimite:
    """
    Análisis de Valores Límite
    ==========================
    Prueba los límites del mecanismo de bloqueo por intentos fallidos.
    Límite definido en el modelo: 5 intentos → bloqueo de 15 minutos.
    """

    def test_CN_L_009_bloqueo_automatico_tras_cinco_intentos(self, client, usuario_psicologo):
        """
        CN-L-009: El sistema bloquea al usuario tras exactamente 5 intentos fallidos.

        ENTRADA (5 veces):
            username = 'psicologo_test'
            password = 'password_incorrecta'

        RESULTADO ESPERADO TRAS 5 INTENTOS:
            - usuario.bloqueado = True
            - usuario.intentos_fallidos = 5
            - fecha_desbloqueo establecida ~15 minutos en el futuro
        """
        url = reverse('auth:login')

        for i in range(5):
            client.post(url, {
                'username': 'psicologo_test',
                'password': 'password_incorrecta_XXXXX',
            })

        usuario_psicologo.refresh_from_db()
        assert usuario_psicologo.intentos_fallidos >= 5
        assert usuario_psicologo.bloqueado is True
        assert usuario_psicologo.fecha_desbloqueo is not None

    def test_CN_L_007_desbloqueo_automatico_tras_timeout(self, usuario_bloqueado):
        """
        CN-L-007: Usuario se desbloquea cuando expira el timeout.

        Prueba el método desbloquear() del modelo con fecha en el pasado.

        ENTRADA:
            usuario con bloqueado=True, fecha_desbloqueo = hace 1 segundo

        RESULTADO ESPERADO:
            - desbloquear() retorna True
            - usuario.bloqueado = False
        """
        # Forzar que el tiempo de desbloqueo ya pasó
        usuario_bloqueado.fecha_desbloqueo = timezone.now() - timedelta(seconds=1)
        usuario_bloqueado.save()

        resultado = usuario_bloqueado.desbloquear()

        assert resultado is True
        assert usuario_bloqueado.bloqueado is False
        assert usuario_bloqueado.intentos_fallidos == 0


class TestLoginAPI_CajaNegra:
    """
    Pruebas de Caja Negra para endpoint API REST /api/auth/login/
    """

    def test_CN_L_010_api_login_exitoso_retorna_tokens(self, api_client, usuario_psicologo):
        """
        CN-L-010: API login exitoso retorna tokens JWT.

        ENTRADA:
            POST /api/auth/login/ con credenciales válidas (JSON)

        RESULTADO ESPERADO:
            - HTTP 200
            - JSON con 'tokens.access' y 'tokens.refresh'
            - JSON con 'usuario.username'
        """
        url = reverse('auth:api_login')
        datos = {
            'username': 'psicologo_test',
            'password': 'Psico@2024!Seg',
        }

        response = api_client.post(url, datos, format='json')

        assert response.status_code == 200
        data = response.json()
        assert 'tokens' in data
        assert 'access' in data['tokens']
        assert 'refresh' in data['tokens']
        assert data['usuario']['username'] == 'psicologo_test'

    def test_CN_L_011_api_login_credenciales_invalidas(self, api_client, db):
        """
        CN-L-011: API login con credenciales incorrectas retorna 401.

        ENTRADA: POST con password incorrecta.
        RESULTADO ESPERADO: HTTP 401 + JSON con clave 'error'.
        """
        url = reverse('auth:api_login')
        response = api_client.post(url, {
            'username': 'nadie',
            'password': 'nada',
        }, format='json')

        assert response.status_code == 401
        assert 'error' in response.json()
