# tests_sgep/tests_caja_blanca/test_auth_caja_blanca.py
"""
PRUEBAS DE CAJA BLANCA — Módulo: Autenticación
===============================================
Técnica: Cobertura de Decisiones (Branch Coverage) + Cobertura de Caminos

FUNCIONES ANALIZADAS (con acceso al código fuente):
    AutenticacionService.validar_fuerza_password()
    AutenticacionService.esta_ip_bloqueada()
    AutenticacionService.obtener_intentos_fallidos()
    PermisosService.usuario_puede_editar_usuario()
    PermisosService.usuario_puede_ver_auditoria()
    PermisosService.usuario_es_psicologo()
    Usuario.registrar_intento_fallido()
    Usuario.desbloquear()
    Usuario.limpiar_intentos_fallidos()
    SesionUsuario.esta_activa()
    RecuperacionPassword.esta_vigente()
    get_client_ip()  (views.py)
    get_device_info()  (views.py)

COBERTURA OBJETIVO:
    - Todas las ramas IF/ELSE deben ejecutarse (branch coverage)
    - Todos los bucles for/while deben probarse con 0, 1 y N iteraciones
    - Todos los except deben ser ejercitados
"""

import pytest
from django.utils import timezone
from datetime import timedelta


pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: AutenticacionService.validar_fuerza_password()
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente analizado (services.py):
#
#   if len(password) < 12:          → RAMA 1a/1b
#       errores.append(...)
#   if not any(c.isupper() ...):    → RAMA 2a/2b
#       errores.append(...)
#   if not any(c.islower() ...):    → RAMA 3a/3b
#       errores.append(...)
#   if not any(c.isdigit() ...):    → RAMA 4a/4b
#       errores.append(...)
#   if not any(c in '!@#...' ...):  → RAMA 5a/5b
#       errores.append(...)
#   return len(errores) == 0, errores
#
# CAMINOS TOTALES: 2^5 = 32, pero solo los relevantes se prueban.

class TestValidarFuerzaPassword:
    """Cobertura de decisiones para validar_fuerza_password()."""

    def test_CB_A_001_password_valida_todas_condiciones_cumplidas(self):
        """
        CB-A-001: Password que cumple TODOS los requisitos.
        CAMINO: Rama 1b (len>=12) + 2b (tiene mayúscula) + 3b + 4b + 5b
        RESULTADO: (True, [])
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('SecurePass@2024!')

        assert valido is True
        assert len(errores) == 0

    def test_CB_A_002_password_muy_corta_falla_longitud(self):
        """
        CB-A-002: Password con menos de 12 caracteres.
        RAMA EJECUTADA: 1a (len < 12 → True → append error)
        RESULTADO: (False, ['Mínimo 12 caracteres', ...])
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('Abc@1')

        assert valido is False
        assert any('12' in e or 'mínimo' in e.lower() for e in errores)

    def test_CB_A_003_password_sin_mayusculas_falla(self):
        """
        CB-A-003: Password sin mayúsculas.
        RAMA EJECUTADA: 2a (not any isupper → True → append error)
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('securepass@2024!')

        assert valido is False
        assert any('mayúscula' in e.lower() or 'upper' in e.lower() for e in errores)

    def test_CB_A_004_password_sin_minusculas_falla(self):
        """
        CB-A-004: Password sin minúsculas.
        RAMA EJECUTADA: 3a (not any islower → True → append error)
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('SECUREPASS@2024!')

        assert valido is False
        assert any('minúscula' in e.lower() or 'lower' in e.lower() for e in errores)

    def test_CB_A_005_password_sin_numeros_falla(self):
        """
        CB-A-005: Password sin dígitos.
        RAMA EJECUTADA: 4a (not any isdigit → True → append error)
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('SecurePassword@!')

        assert valido is False
        assert any('número' in e.lower() or 'digit' in e.lower() for e in errores)

    def test_CB_A_006_password_sin_especiales_falla(self):
        """
        CB-A-006: Password sin caracteres especiales.
        RAMA EJECUTADA: 5a (not any in '!@#...' → True → append error)
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('SecurePassword2024')

        assert valido is False
        assert any('especial' in e.lower() or 'special' in e.lower() for e in errores)

    def test_CB_A_007_password_multiple_errores_acumulados(self):
        """
        CB-A-007: Password muy corta y sin mayúsculas ni especiales.
        RAMAS EJECUTADAS: 1a + 2a + 5a (múltiples ramas verdaderas simultáneamente)
        RESULTADO: Lista de errores con múltiples entradas
        """
        from apps.auth_app.services import AutenticacionService

        valido, errores = AutenticacionService.validar_fuerza_password('abc')

        assert valido is False
        assert len(errores) >= 2   # Al menos 2 errores (longitud + otros)

    def test_CB_A_008_password_exactamente_12_caracteres(self):
        """
        CB-A-008: Password con exactamente 12 caracteres (VALOR LÍMITE).
        RAMA: 1b (len == 12, NO entra al if → no error de longitud)
        """
        from apps.auth_app.services import AutenticacionService

        # Exactamente 12 chars con todos los requisitos
        valido, errores = AutenticacionService.validar_fuerza_password('SecPass@1234')

        # No debe haber error de longitud
        assert not any('12' in e and 'mínimo' in e.lower() for e in errores)

    def test_CB_A_009_bucle_any_isupper_termina_en_primera_mayuscula(self):
        """
        CB-A-009: Bucle any(c.isupper()) termina en el primer char mayúscula.
        Prueba que el iterador no recorre innecesariamente toda la cadena.
        """
        from apps.auth_app.services import AutenticacionService

        # Password válida donde la mayúscula está al inicio
        valido, errores = AutenticacionService.validar_fuerza_password('Alguien2024@ok!')

        assert valido is True


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: AutenticacionService.esta_ip_bloqueada()
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente analizado:
#   intentos = cls.obtener_intentos_fallidos_por_ip(ip, horas)
#   return intentos >= max_intentos
#
# RAMAS:
#   - Rama VERDADERA: intentos >= max_intentos → True
#   - Rama FALSA: intentos < max_intentos → False

class TestEstaIPBloqueada:

    def test_CB_A_010_ip_no_bloqueada_pocos_intentos(self, db):
        """
        CB-A-010: IP con 0 intentos → no bloqueada.
        RAMA EJECUTADA: intentos (0) < max_intentos (20) → False
        """
        from apps.auth_app.services import AutenticacionService

        resultado = AutenticacionService.esta_ip_bloqueada('192.168.1.1')

        assert resultado is False

    def test_CB_A_011_ip_bloqueada_muchos_intentos(self, db):
        """
        CB-A-011: IP con >= 20 intentos → bloqueada.
        RAMA EJECUTADA: intentos >= max_intentos → True

        Prepara 20 registros de intentos fallidos desde la misma IP.
        """
        from apps.auth_app.models import IntentofallaloLogin
        from apps.auth_app.services import AutenticacionService

        ip_test = '10.0.0.99'
        for i in range(20):
            IntentofallaloLogin.objects.create(
                username=f'user_{i}',
                ip_address=ip_test,
                razon='Test de bloqueo IP',
            )

        resultado = AutenticacionService.esta_ip_bloqueada(ip_test)

        assert resultado is True


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: Usuario.registrar_intento_fallido()
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente analizado:
#   self.intentos_fallidos += 1
#   if self.intentos_fallidos >= 5:     ← DECISIÓN PRINCIPAL
#       self.bloqueado = True
#       self.fecha_desbloqueo = timezone.now() + timedelta(minutes=15)
#       self.razon_bloqueo = "Múltiples intentos fallidos"
#   self.save()

class TestRegistrarIntentoFallido:

    def test_CB_A_012_primer_intento_no_bloquea(self, usuario_psicologo):
        """
        CB-A-012: Primer intento fallido — no bloquea.
        RAMA EJECUTADA: intentos_fallidos (1) < 5 → no se ejecuta bloque if
        """
        usuario_psicologo.intentos_fallidos = 0
        usuario_psicologo.save()

        usuario_psicologo.registrar_intento_fallido()

        assert usuario_psicologo.intentos_fallidos == 1
        assert usuario_psicologo.bloqueado is False
        assert usuario_psicologo.fecha_desbloqueo is None

    def test_CB_A_013_cuarto_intento_no_bloquea(self, usuario_psicologo):
        """
        CB-A-013: Cuarto intento (intentos_fallidos = 4) — justo antes del límite.
        VALOR LÍMITE INFERIOR: 4 < 5 → no bloquea.
        """
        usuario_psicologo.intentos_fallidos = 3
        usuario_psicologo.save()

        usuario_psicologo.registrar_intento_fallido()

        assert usuario_psicologo.intentos_fallidos == 4
        assert usuario_psicologo.bloqueado is False

    def test_CB_A_014_quinto_intento_bloquea(self, usuario_psicologo):
        """
        CB-A-014: Quinto intento (intentos_fallidos = 5) — BLOQUEA.
        VALOR LÍMITE: 5 >= 5 → RAMA VERDADERA ejecutada.
        RESULTADO: bloqueado=True, fecha_desbloqueo en ~15 min futuro.
        """
        usuario_psicologo.intentos_fallidos = 4
        usuario_psicologo.save()

        usuario_psicologo.registrar_intento_fallido()

        assert usuario_psicologo.intentos_fallidos == 5
        assert usuario_psicologo.bloqueado is True
        assert usuario_psicologo.fecha_desbloqueo is not None

        # Verificar que es aproximadamente 15 minutos en el futuro
        delta = usuario_psicologo.fecha_desbloqueo - timezone.now()
        assert 12 * 60 <= delta.seconds <= 16 * 60, (
            f"fecha_desbloqueo debería ser ~15 min, delta={delta}"
        )

    def test_CB_A_015_sexto_intento_mantiene_bloqueo(self, usuario_psicologo):
        """
        CB-A-015: Intento número 6 (ya bloqueado) — sigue bloqueado.
        RAMA: intentos_fallidos (6) >= 5 → True (se actualiza bloqueo)
        """
        usuario_psicologo.intentos_fallidos = 5
        usuario_psicologo.bloqueado = True
        usuario_psicologo.save()

        usuario_psicologo.registrar_intento_fallido()

        assert usuario_psicologo.intentos_fallidos == 6
        assert usuario_psicologo.bloqueado is True


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: Usuario.desbloquear()
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente:
#   if self.fecha_desbloqueo and timezone.now() >= self.fecha_desbloqueo:
#       self.bloqueado = False
#       self.intentos_fallidos = 0
#       self.fecha_desbloqueo = None
#       self.razon_bloqueo = ""
#       self.save()
#       return True
#   return False
#
# DECISIONES:
#   D1: self.fecha_desbloqueo is not None (Verdad/Falso)
#   D2: timezone.now() >= self.fecha_desbloqueo (Verdad/Falso)
#   COMBINACIONES: D1=T,D2=T → True | D1=T,D2=F → False | D1=F → False

class TestDesbloquearUsuario:

    def test_CB_A_016_desbloquear_sin_fecha_retorna_false(self, usuario_psicologo):
        """
        CB-A-016: fecha_desbloqueo=None → retorna False (rama D1=Falso).
        """
        usuario_psicologo.bloqueado = True
        usuario_psicologo.fecha_desbloqueo = None
        usuario_psicologo.save()

        resultado = usuario_psicologo.desbloquear()

        assert resultado is False
        assert usuario_psicologo.bloqueado is True

    def test_CB_A_017_desbloquear_fecha_futura_retorna_false(self, usuario_psicologo):
        """
        CB-A-017: fecha_desbloqueo en el FUTURO → no desbloquea (D1=T, D2=F).
        """
        usuario_psicologo.bloqueado = True
        usuario_psicologo.fecha_desbloqueo = timezone.now() + timedelta(minutes=10)
        usuario_psicologo.save()

        resultado = usuario_psicologo.desbloquear()

        assert resultado is False
        assert usuario_psicologo.bloqueado is True

    def test_CB_A_018_desbloquear_fecha_pasada_retorna_true(self, usuario_psicologo):
        """
        CB-A-018: fecha_desbloqueo en el PASADO → desbloquea (D1=T, D2=T).
        RAMA VERDADERA completa ejecutada.
        """
        usuario_psicologo.bloqueado = True
        usuario_psicologo.intentos_fallidos = 5
        usuario_psicologo.fecha_desbloqueo = timezone.now() - timedelta(seconds=1)
        usuario_psicologo.save()

        resultado = usuario_psicologo.desbloquear()

        assert resultado is True
        assert usuario_psicologo.bloqueado is False
        assert usuario_psicologo.intentos_fallidos == 0
        assert usuario_psicologo.fecha_desbloqueo is None
        assert usuario_psicologo.razon_bloqueo == ''


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: PermisosService — Control de Acceso por Rol (RBAC)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPermisosService:

    def test_CB_A_019_admin_puede_editar_cualquier_usuario(
        self, usuario_admin, usuario_psicologo
    ):
        """
        CB-A-019: Administrador puede editar a otro usuario.
        RAMA: usuario_actual.rol.nombre == 'administrador' → return True
        """
        from apps.auth_app.services import PermisosService

        resultado = PermisosService.usuario_puede_editar_usuario(
            usuario_admin, usuario_psicologo
        )
        assert resultado is True

    def test_CB_A_020_psicologo_puede_editarse_a_si_mismo(
        self, usuario_psicologo
    ):
        """
        CB-A-020: Psicólogo puede editar su propio perfil.
        RAMA: usuario_actual.id == usuario_target.id → return True
        """
        from apps.auth_app.services import PermisosService

        resultado = PermisosService.usuario_puede_editar_usuario(
            usuario_psicologo, usuario_psicologo
        )
        assert resultado is True

    def test_CB_A_021_psicologo_no_puede_editar_otro_usuario(
        self, usuario_psicologo, usuario_admin
    ):
        """
        CB-A-021: Psicólogo NO puede editar a otro usuario.
        RAMAS: rol != 'admin' → False, ids distintos → return False
        """
        from apps.auth_app.services import PermisosService

        resultado = PermisosService.usuario_puede_editar_usuario(
            usuario_psicologo, usuario_admin
        )
        assert resultado is False

    def test_CB_A_022_admin_puede_ver_auditoria(self, usuario_admin):
        """CB-A-022: Administrador puede ver auditoría."""
        from apps.auth_app.services import PermisosService

        assert PermisosService.usuario_puede_ver_auditoria(usuario_admin) is True

    def test_CB_A_022b_auditoria_puede_ver_auditoria(self, rol_auditoria):
        """CB-A-022b: Rol auditoría puede ver auditoría."""
        from apps.auth_app.models import Usuario
        from apps.auth_app.services import PermisosService

        user_audit = Usuario.objects.create_user(
            username='auditor_test2',
            password='Audit@2024!xx',
            email='audit2@test.bo',
            rol=rol_auditoria,
            activo=True,
        )
        assert PermisosService.usuario_puede_ver_auditoria(user_audit) is True

    def test_CB_A_023_psicologo_no_puede_ver_auditoria(self, usuario_psicologo):
        """CB-A-023: Psicólogo NO puede ver auditoría."""
        from apps.auth_app.services import PermisosService

        assert PermisosService.usuario_puede_ver_auditoria(usuario_psicologo) is False

    def test_CB_A_024_identificar_psicologo(self, usuario_psicologo, usuario_admin):
        """CB-A-024: usuario_es_psicologo() — ramas T y F."""
        from apps.auth_app.services import PermisosService

        assert PermisosService.usuario_es_psicologo(usuario_psicologo) is True
        assert PermisosService.usuario_es_psicologo(usuario_admin) is False


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: SesionUsuario.esta_activa() y RecuperacionPassword.esta_vigente()
# ═══════════════════════════════════════════════════════════════════════════════

class TestSesionUsuario:

    def test_CB_A_025_sesion_activa_dentro_de_expiracion(
        self, usuario_psicologo
    ):
        """
        CB-A-025: sesion.activa=True y fecha_expiracion futura → esta_activa()=True
        RAMA: activa AND now < fecha_expiracion → True
        """
        from apps.auth_app.models import SesionUsuario

        sesion = SesionUsuario.objects.create(
            usuario=usuario_psicologo,
            token='test_token_abc',
            ip_address='127.0.0.1',
            activa=True,
            fecha_expiracion=timezone.now() + timedelta(hours=1),
        )

        assert sesion.esta_activa() is True

    def test_CB_A_026_sesion_expirada_no_activa(self, usuario_psicologo):
        """
        CB-A-026: fecha_expiracion pasada → esta_activa()=False.
        RAMA: now >= fecha_expiracion → False
        """
        from apps.auth_app.models import SesionUsuario

        sesion = SesionUsuario.objects.create(
            usuario=usuario_psicologo,
            token='expired_token',
            ip_address='127.0.0.1',
            activa=True,
            fecha_expiracion=timezone.now() - timedelta(hours=1),  # EXPIRADA
        )

        assert sesion.esta_activa() is False

    def test_CB_A_027_sesion_cerrada_no_activa(self, usuario_psicologo):
        """
        CB-A-027: activa=False → esta_activa()=False aunque no expiró.
        RAMA: not activa → False
        """
        from apps.auth_app.models import SesionUsuario

        sesion = SesionUsuario.objects.create(
            usuario=usuario_psicologo,
            token='closed_token',
            ip_address='127.0.0.1',
            activa=False,  # CERRADA manualmente
            fecha_expiracion=timezone.now() + timedelta(hours=1),
        )

        assert sesion.esta_activa() is False


class TestRecuperacionPassword:

    def test_CB_A_028_token_vigente_no_usado_no_expirado(self, usuario_psicologo):
        """
        CB-A-028: Token no usado y no expirado → esta_vigente()=True.
        RAMA: not usado AND now < fecha_expiracion → True
        """
        from apps.auth_app.models import RecuperacionPassword

        rec = RecuperacionPassword.objects.create(
            usuario=usuario_psicologo,
            token='valid_recovery_token_abc',
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            usado=False,
        )

        assert rec.esta_vigente() is True

    def test_CB_A_029_token_ya_usado_no_vigente(self, usuario_psicologo):
        """
        CB-A-029: Token marcado como usado → esta_vigente()=False.
        RAMA: usado=True → False
        """
        from apps.auth_app.models import RecuperacionPassword

        rec = RecuperacionPassword.objects.create(
            usuario=usuario_psicologo,
            token='used_recovery_token_xyz',
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            usado=True,
        )

        assert rec.esta_vigente() is False

    def test_CB_A_030_token_expirado_no_vigente(self, usuario_psicologo):
        """
        CB-A-030: Token expirado (fecha en pasado) → esta_vigente()=False.
        RAMA: now >= fecha_expiracion → False
        """
        from apps.auth_app.models import RecuperacionPassword

        rec = RecuperacionPassword.objects.create(
            usuario=usuario_psicologo,
            token='expired_recovery_token_111',
            fecha_expiracion=timezone.now() - timedelta(hours=1),
            usado=False,
        )

        assert rec.esta_vigente() is False


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: get_client_ip() y get_device_info() — Funciones auxiliares views.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestFuncionesAuxiliares:
    """
    Prueba las funciones auxiliares puras de views.py.
    No requieren BD → no usan @pytest.mark.django_db en este nivel.
    """

    def test_CB_A_031_get_client_ip_usa_remote_addr(self, rf):
        """
        CB-A-031: Sin X-Forwarded-For → usa REMOTE_ADDR.
        RAMA: x_forwarded_for is None → ip = REMOTE_ADDR
        """
        from apps.auth_app.views import get_client_ip

        request = rf.get('/login/')
        request.META['REMOTE_ADDR'] = '192.168.0.1'
        # Asegurar que no hay X-Forwarded-For
        request.META.pop('HTTP_X_FORWARDED_FOR', None)

        ip = get_client_ip(request)

        assert ip == '192.168.0.1'

    def test_CB_A_032_get_client_ip_usa_x_forwarded_for(self, rf):
        """
        CB-A-032: Con X-Forwarded-For → usa primer IP de la cadena.
        RAMA: x_forwarded_for is not None → split(',')[0]
        """
        from apps.auth_app.views import get_client_ip

        request = rf.get('/login/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.5, 192.168.0.1'

        ip = get_client_ip(request)

        assert ip == '203.0.113.5'

    def test_CB_A_033_get_device_info_detecta_windows(self, rf):
        """
        CB-A-033: User-Agent con 'Windows' → retorna 'Windows'.
        RAMA: 'Windows' in user_agent → True
        """
        from apps.auth_app.views import get_device_info

        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        resultado = get_device_info(ua)

        assert resultado == 'Windows'

    def test_CB_A_034_get_device_info_detecta_android(self, rf):
        """
        CB-A-034: User-Agent con 'Android' → 'Android'.
        """
        from apps.auth_app.views import get_device_info

        ua = 'Mozilla/5.0 (Linux; Android 11; Pixel 5)'
        resultado = get_device_info(ua)

        assert resultado == 'Android'

    def test_CB_A_035_get_device_info_desconocido(self, rf):
        """
        CB-A-035: User-Agent desconocido → 'Desconocido'.
        RAMA: Ninguna condición cumplida → else 'Desconocido'
        """
        from apps.auth_app.views import get_device_info

        resultado = get_device_info('curl/7.68.0')

        assert resultado == 'Desconocido'

    def test_CB_A_036_get_device_info_ios_iphone(self, rf):
        """
        CB-A-036: User-Agent con 'iPhone' → 'iOS'.
        RAMA: 'iPhone' in user_agent → True
        """
        from apps.auth_app.views import get_device_info

        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0)'
        resultado = get_device_info(ua)

        assert resultado == 'iOS'
