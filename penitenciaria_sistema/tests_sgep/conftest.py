# tests_sgep/conftest.py
"""
Configuración global de pytest para el SGEP.
Define fixtures compartidas entre todos los módulos de prueba.

Uso:
    pytest tests_sgep/ -v
    pytest tests_sgep/ --cov=apps --cov-report=html
"""

import pytest
from django.utils import timezone
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES DE ROLES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def rol_administrador(db):
    """Crea rol administrador en BD de prueba."""
    from apps.auth_app.models import Rol
    rol, _ = Rol.objects.get_or_create(
        nombre='administrador',
        defaults={'descripcion': 'Administrador del sistema', 'activo': True}
    )
    return rol


@pytest.fixture
def rol_psicologo(db):
    """Crea rol psicólogo en BD de prueba."""
    from apps.auth_app.models import Rol
    rol, _ = Rol.objects.get_or_create(
        nombre='psicologo',
        defaults={'descripcion': 'Psicólogo del centro', 'activo': True}
    )
    return rol


@pytest.fixture
def rol_director(db):
    """Crea rol director en BD de prueba."""
    from apps.auth_app.models import Rol
    rol, _ = Rol.objects.get_or_create(
        nombre='director',
        defaults={'descripcion': 'Director del centro penitenciario', 'activo': True}
    )
    return rol


@pytest.fixture
def rol_auditoria(db):
    """Crea rol auditoría en BD de prueba."""
    from apps.auth_app.models import Rol
    rol, _ = Rol.objects.get_or_create(
        nombre='auditoria',
        defaults={'descripcion': 'Auditoría ISO 27001', 'activo': True}
    )
    return rol


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES DE USUARIOS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario_admin(db, rol_administrador):
    """Crea usuario administrador activo."""
    from apps.auth_app.models import Usuario
    usuario = Usuario.objects.create_user(
        username='admin_test',
        password='AdminTest@2024!',
        email='admin@test.bo',
        first_name='Admin',
        last_name='Sistema',
        rol=rol_administrador,
        activo=True,
        bloqueado=False,
    )
    return usuario


@pytest.fixture
def usuario_psicologo(db, rol_psicologo):
    """Crea usuario psicólogo activo."""
    from apps.auth_app.models import Usuario
    usuario = Usuario.objects.create_user(
        username='psicologo_test',
        password='Psico@2024!Seg',
        email='psicologo@test.bo',
        first_name='Juan',
        last_name='Pérez',
        rol=rol_psicologo,
        activo=True,
        bloqueado=False,
        especialidad='Psicología Forense',
    )
    return usuario


@pytest.fixture
def usuario_inactivo(db, rol_psicologo):
    """Crea usuario inactivo para pruebas de acceso."""
    from apps.auth_app.models import Usuario
    usuario = Usuario.objects.create_user(
        username='inactivo_test',
        password='InacTest@2024!',
        email='inactivo@test.bo',
        first_name='Usuario',
        last_name='Inactivo',
        rol=rol_psicologo,
        activo=False,
        bloqueado=False,
    )
    return usuario


@pytest.fixture
def usuario_bloqueado(db, rol_psicologo):
    """Crea usuario bloqueado por intentos fallidos."""
    from apps.auth_app.models import Usuario
    usuario = Usuario.objects.create_user(
        username='bloqueado_test',
        password='BloquTest@2024!',
        email='bloqueado@test.bo',
        first_name='Usuario',
        last_name='Bloqueado',
        rol=rol_psicologo,
        activo=True,
        bloqueado=True,
        intentos_fallidos=5,
        fecha_desbloqueo=timezone.now() + timedelta(minutes=10),
        razon_bloqueo='Múltiples intentos fallidos de login',
    )
    return usuario


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES DE INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def interno_activo(db):
    """Crea un interno activo para pruebas."""
    from apps.internos_app.models import Interno
    interno = Interno.objects.create(
        nombre='Carlos',
        apellido='Mamani',
        cedula='1234567',
        fecha_nacimiento='1985-03-15',
        sexo='M',
        estado='procesado',
        delito='robo agravado',
        centro_penitenciario='San Pedro',
        celda='B-12',
        observaciones='Sin observaciones especiales.',
    )
    return interno


@pytest.fixture
def interno_condenado(db):
    """Crea un interno condenado para pruebas."""
    from apps.internos_app.models import Interno
    interno = Interno.objects.create(
        nombre='María',
        apellido='Flores',
        cedula='7654321',
        fecha_nacimiento='1990-07-20',
        sexo='F',
        estado='condenado',
        delito='tráfico de sustancias controladas',
        centro_penitenciario='Miraflores',
        celda='A-05',
    )
    return interno


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES DE EVALUACIONES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def evaluacion_pendiente(db, interno_activo, usuario_psicologo):
    """Crea una evaluación en estado pendiente."""
    from apps.evaluaciones_app.models import Evaluacion
    evaluacion = Evaluacion.objects.create(
        titulo='Evaluación de Ingreso - Carlos Mamani',
        interno=interno_activo,
        psicoplogo=usuario_psicologo,
        estado='pendiente',
        completada=False,
    )
    return evaluacion


@pytest.fixture
def evaluacion_completada(db, interno_activo, usuario_psicologo):
    """Crea una evaluación completada con resultados."""
    from apps.evaluaciones_app.models import Evaluacion
    evaluacion = Evaluacion.objects.create(
        titulo='Evaluación Periódica - Carlos Mamani',
        interno=interno_activo,
        psicoplogo=usuario_psicologo,
        estado='completada',
        completada=True,
        nivel_riesgo='medio',
        calificacion_riesgo=45.0,
        resultados={
            'depresion_severa': False,
            'ansiedad_severa': True,
            'reincidencias': 1,
            'apoyo_familiar': True,
        },
        fecha_completada=timezone.now(),
    )
    return evaluacion


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES DE CLIENTES HTTP
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client_autenticado_admin(client, usuario_admin):
    """Cliente HTTP autenticado como administrador."""
    client.force_login(usuario_admin)
    return client


@pytest.fixture
def client_autenticado_psicologo(client, usuario_psicologo):
    """Cliente HTTP autenticado como psicólogo."""
    client.force_login(usuario_psicologo)
    return client


@pytest.fixture
def api_client():
    """Cliente DRF para pruebas de API REST."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def api_client_autenticado(api_client, usuario_psicologo):
    """Cliente DRF autenticado como psicólogo."""
    api_client.force_authenticate(user=usuario_psicologo)
    return api_client
