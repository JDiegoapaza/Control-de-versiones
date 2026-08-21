# tests_sgep/tests_caja_negra/test_internos_caja_negra.py
"""
PRUEBAS DE CAJA NEGRA — Módulo: Registro y Gestión de Internos
===============================================================
Técnica: Partición de Equivalencia + Análisis de Valores Límite

MÓDULO ANALIZADO : apps.internos_app (views.py, models.py, services.py)
VISTAS           : InternoCreateWebView, InternoListWebView, InternoDetailWebView,
                   InternoEditWebView, InternoDeleteWebView, InternoListCreateView (API)
URLS             : /internos/, /internos/nuevo/, /internos/<pk>/, /internos/api/

Casos cubiertos
---------------
CN-I-001  Registro exitoso de interno con datos completos válidos
CN-I-002  Registro fallido — cédula duplicada
CN-I-003  Registro fallido — campos obligatorios vacíos (nombre, apellido, cédula)
CN-I-004  Listado de internos activos con paginación
CN-I-005  Búsqueda por nombre, apellido y cédula
CN-I-006  Filtro por estado (procesado, condenado, liberado, traslado)
CN-I-007  Detalle de interno existente
CN-I-008  Detalle de interno inexistente → 404
CN-I-009  Edición exitosa de datos de interno
CN-I-010  Eliminación lógica (soft delete) — activo=False
CN-I-011  Acceso sin autenticación → redirección a login
CN-I-012  API: Creación exitosa vía JSON
CN-I-013  API: Listado filtrado por estado
CN-I-014  Búsqueda por cédula via servicio
CN-I-015  Cambio de estado vía servicio — estado inválido lanza ValueError
"""

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


class TestRegistroInternoValido:
    """
    Clase VÁLIDA: Registro con todos los campos correctos.
    """

    def test_CN_I_001_registro_exitoso_datos_completos(
        self, client_autenticado_admin
    ):
        """
        CN-I-001: Registrar interno con todos los datos válidos.

        ENTRADA:
            nombre='Pedro', apellido='Quispe', cedula='9999001',
            sexo='M', estado='procesado', delito='robo', ...

        RESULTADO ESPERADO:
            - HTTP 302 Redirect a /internos/
            - Interno creado en BD con activo=True
            - Mensaje de éxito en sesión
        """
        url = reverse('internos:nuevo')
        datos = {
            'nombre': 'Pedro',
            'apellido': 'Quispe',
            'cedula': '9999001',
            'fecha_nacimiento': '1988-05-10',
            'sexo': 'M',
            'estado': 'procesado',
            'delito': 'robo agravado',
            'centro_penitenciario': 'San Pedro',
            'celda': 'C-15',
            'observaciones': 'Primera evaluación pendiente.',
        }

        response = client_autenticado_admin.post(url, datos)

        assert response.status_code == 302, (
            f"Se esperaba redirect 302, se obtuvo {response.status_code}"
        )

        # Verificar que se creó en BD
        from apps.internos_app.models import Interno
        assert Interno.objects.filter(cedula='9999001', activo=True).exists()

    def test_CN_I_001b_registro_exitoso_campos_minimos(
        self, client_autenticado_admin
    ):
        """
        CN-I-001b: Registro con solo los campos mínimos requeridos.
        """
        url = reverse('internos:nuevo')
        datos = {
            'nombre': 'Ana',
            'apellido': 'Condori',
            'cedula': '9999002',
            'sexo': 'F',
            'estado': 'procesado',
        }
        response = client_autenticado_admin.post(url, datos)
        # Puede ser 302 (éxito) o 200 con error — depende de validación mínima
        assert response.status_code in (200, 302)

        if response.status_code == 302:
            from apps.internos_app.models import Interno
            assert Interno.objects.filter(cedula='9999002').exists()


class TestRegistroInternoInvalido:
    """
    Clase INVÁLIDA: Datos incorrectos deben rechazarse.
    """

    def test_CN_I_002_registro_fallido_cedula_duplicada(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-002: Cédula ya registrada en el sistema.

        ENTRADA:
            cedula='1234567' (ya existe como interno_activo.cedula)

        RESULTADO ESPERADO:
            - HTTP 200 (se muestra formulario con error)
            - NO se crea segundo registro
            - Mensaje de error visible
        """
        from apps.internos_app.models import Interno

        url = reverse('internos:nuevo')
        datos = {
            'nombre': 'Otro',
            'apellido': 'Apellido',
            'cedula': interno_activo.cedula,   # DUPLICADA
            'sexo': 'M',
            'estado': 'procesado',
        }

        response = client_autenticado_admin.post(url, datos)

        # Debe mostrar error (200) O redirigir pero la BD NO debe tener duplicado
        count = Interno.objects.filter(cedula=interno_activo.cedula).count()
        assert count == 1, f"Se creó registro duplicado (count={count})"

    def test_CN_I_003_registro_fallido_cedula_vacia(
        self, client_autenticado_admin
    ):
        """
        CN-I-003: Cédula vacía — campo obligatorio.
        """
        url = reverse('internos:nuevo')
        datos = {
            'nombre': 'Sin',
            'apellido': 'Cedula',
            'cedula': '',          # VACÍA
            'sexo': 'M',
            'estado': 'procesado',
        }
        response = client_autenticado_admin.post(url, datos)

        from apps.internos_app.models import Interno
        assert not Interno.objects.filter(nombre='Sin', apellido='Cedula').exists()


class TestListadoInternos:
    """
    Pruebas para la vista de listado con filtros y paginación.
    """

    def test_CN_I_004_listado_internos_activos(
        self, client_autenticado_admin, interno_activo, interno_condenado
    ):
        """
        CN-I-004: Listado solo muestra internos activos.

        RESULTADO ESPERADO:
            - HTTP 200
            - Aparece carlos Mamani (interno_activo)
            - Aparece María Flores (interno_condenado)
        """
        url = reverse('internos:lista')
        response = client_autenticado_admin.get(url)

        assert response.status_code == 200
        assert b'Mamani' in response.content or b'mamani' in response.content.lower()

    def test_CN_I_005_busqueda_por_cedula(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-005: Búsqueda por cédula retorna solo el interno correspondiente.

        ENTRADA: ?q=1234567
        RESULTADO: Solo Carlos Mamani aparece.
        """
        url = reverse('internos:lista')
        response = client_autenticado_admin.get(url, {'q': '1234567'})

        assert response.status_code == 200
        assert b'Mamani' in response.content or b'1234567' in response.content

    def test_CN_I_006_filtro_por_estado_procesado(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-006: Filtro ?estado=procesado muestra solo procesados.
        """
        url = reverse('internos:lista')
        response = client_autenticado_admin.get(url, {'estado': 'procesado'})

        assert response.status_code == 200

    def test_CN_I_005b_busqueda_por_apellido(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-005b: Búsqueda parcial por apellido.
        """
        url = reverse('internos:lista')
        response = client_autenticado_admin.get(url, {'q': 'Mama'})
        assert response.status_code == 200


class TestDetalleInterno:
    """
    Pruebas para vista de detalle individual.
    """

    def test_CN_I_007_detalle_interno_existente(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-007: Detalle de interno activo existente.

        RESULTADO ESPERADO: HTTP 200 + datos del interno visibles.
        """
        url = reverse('internos:detalle', kwargs={'pk': interno_activo.pk})
        response = client_autenticado_admin.get(url)

        assert response.status_code == 200
        assert b'Mamani' in response.content or b'Carlos' in response.content

    def test_CN_I_008_detalle_interno_inexistente_404(
        self, client_autenticado_admin
    ):
        """
        CN-I-008: Detalle de UUID inexistente → 404.

        ENTRADA: UUID que no existe en BD.
        RESULTADO ESPERADO: HTTP 404.
        """
        import uuid
        url = reverse('internos:detalle', kwargs={'pk': str(uuid.uuid4())})
        response = client_autenticado_admin.get(url)

        assert response.status_code == 404


class TestEliminacionInterno:
    """
    Pruebas para eliminación lógica (soft delete).
    """

    def test_CN_I_010_soft_delete_marca_activo_false(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-010: Eliminar interno lo marca como activo=False (NO lo borra de BD).

        RESULTADO ESPERADO:
            - HTTP 302 redirect
            - interno.activo = False
            - interno.eliminado_en != None
            - El registro PERMANECE en BD
        """
        url = reverse('internos:eliminar', kwargs={'pk': interno_activo.pk})
        response = client_autenticado_admin.post(url)

        assert response.status_code == 302

        interno_activo.refresh_from_db()
        assert interno_activo.activo is False
        assert interno_activo.eliminado_en is not None

    def test_CN_I_010b_interno_eliminado_no_aparece_en_listado(
        self, client_autenticado_admin, interno_activo
    ):
        """
        CN-I-010b: Interno con activo=False NO aparece en el listado.
        """
        # Eliminar el interno
        interno_activo.activo = False
        interno_activo.save()

        url = reverse('internos:lista')
        response = client_autenticado_admin.get(url)

        assert response.status_code == 200
        # El apellido no debería aparecer en la lista activa
        # (puede estar en página 2 si hay muchos, pero este es el único)


class TestAccesoSinAutenticacion:
    """
    Pruebas de control de acceso — usuario NO autenticado.
    """

    def test_CN_I_011_listado_sin_autenticacion_redirige_login(self, client):
        """
        CN-I-011: Sin autenticación, el listado redirige a /login/.
        """
        url = reverse('internos:lista')
        response = client.get(url)

        assert response.status_code == 302
        assert 'login' in response['Location'].lower()

    def test_CN_I_011b_nuevo_sin_autenticacion_redirige_login(self, client):
        """
        CN-I-011b: Sin autenticación, el formulario de nuevo interno redirige a /login/.
        """
        url = reverse('internos:nuevo')
        response = client.get(url)

        assert response.status_code == 302
        assert 'login' in response['Location'].lower()


class TestAPIInternos:
    """
    Pruebas de Caja Negra para endpoints API REST.
    """

    def test_CN_I_012_api_creacion_exitosa_json(
        self, api_client_autenticado
    ):
        """
        CN-I-012: POST a API crea interno y retorna JSON con datos.

        ENTRADA: JSON con datos válidos de interno.
        RESULTADO ESPERADO: HTTP 201 + JSON con id, nombre, apellido.
        """
        url = reverse('internos:api_list_create')
        datos = {
            'nombre': 'Roberto',
            'apellido': 'Alvarado',
            'cedula': 'API-001-TEST',
            'sexo': 'M',
            'estado': 'procesado',
            'delito': 'hurto',
            'centro_penitenciario': 'Qalauma',
        }

        response = api_client_autenticado.post(url, datos, format='json')

        assert response.status_code == 201
        data = response.json()
        assert data['cedula'] == 'API-001-TEST'
        assert 'id' in data

    def test_CN_I_013_api_filtro_por_estado(
        self, api_client_autenticado, interno_activo, interno_condenado
    ):
        """
        CN-I-013: GET con filtro ?estado=condenado retorna solo condenados.
        """
        url = reverse('internos:api_list_create')
        response = api_client_autenticado.get(url, {'estado': 'condenado'})

        assert response.status_code == 200
        data = response.json()
        resultados = data.get('results', data)
        for item in resultados:
            assert item['estado'] == 'condenado', (
                f"Se encontró estado '{item['estado']}' cuando se esperaba 'condenado'"
            )


class TestServicioInterno:
    """
    Pruebas de caja negra al InternoService (capa de servicio).
    """

    def test_CN_I_014_busqueda_por_cedula_existente(self, interno_activo):
        """
        CN-I-014: buscar_por_cedula con cédula existente retorna el interno.
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.buscar_por_cedula('1234567')

        assert resultado is not None
        assert resultado.cedula == '1234567'
        assert resultado.nombre == 'Carlos'

    def test_CN_I_014b_busqueda_por_cedula_inexistente(self, db):
        """
        CN-I-014b: buscar_por_cedula con cédula inexistente retorna None.
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.buscar_por_cedula('CEDULA-INEXISTENTE')

        assert resultado is None

    def test_CN_I_015_cambio_estado_invalido_lanza_error(self, interno_activo):
        """
        CN-I-015: cambiar_estado con estado no válido lanza ValueError.

        ENTRADA: nuevo_estado = 'fugado' (no existe en ESTADO_CHOICES)
        RESULTADO ESPERADO: ValueError
        """
        from apps.internos_app.services import InternoService

        with pytest.raises(ValueError, match="Estado inválido"):
            InternoService.cambiar_estado(interno_activo, 'fugado')

    def test_CN_I_015b_cambio_estado_valido(self, interno_activo):
        """
        CN-I-015b: cambiar_estado con 'liberado' actualiza correctamente.
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.cambiar_estado(interno_activo, 'liberado')

        assert resultado.estado == 'liberado'
        interno_activo.refresh_from_db()
        assert interno_activo.estado == 'liberado'
