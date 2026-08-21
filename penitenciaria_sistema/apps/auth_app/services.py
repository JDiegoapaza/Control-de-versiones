# apps/auth_app/services.py
"""
Servicios de Autenticación
Lógica de negocio para login, sesiones y seguridad
"""

import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('apps.seguridad_app')


class AutenticacionService:
    """
    Servicio central de autenticación
    Implementa principios ISO 27001
    """
    
    @staticmethod
    def generar_token_seguro(longitud=32):
        """
        Genera un token seguro usando secrets
        Adecuado para tokens de recuperación de contraseña
        """
        return secrets.token_urlsafe(longitud)
    
    @staticmethod
    def generar_token_recuperacion():
        """
        Genera un token de recuperación de contraseña
        """
        return AutenticacionService.generar_token_seguro(64)
    
    @staticmethod
    def hashear_token(token):
        """
        Hashea un token para almacenamiento seguro
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def validar_fuerza_password(password):
        """
        Valida que la contraseña cumpla requisitos de seguridad
        
        Requisitos:
        - Mínimo 12 caracteres
        - Mayúscula
        - Minúscula
        - Número
        - Carácter especial
        
        Retorna: (válido, mensaje_error)
        """
        
        errores = []
        
        if len(password) < 12:
            errores.append("Mínimo 12 caracteres")
        
        if not any(c.isupper() for c in password):
            errores.append("Debe contener al menos una mayúscula")
        
        if not any(c.islower() for c in password):
            errores.append("Debe contener al menos una minúscula")
        
        if not any(c.isdigit() for c in password):
            errores.append("Debe contener al menos un número")
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errores.append("Debe contener al menos un carácter especial")
        
        return len(errores) == 0, errores
    
    @staticmethod
    def registrar_intento_fallido(username, ip, user_agent, razon):
        """
        Registra un intento fallido de login
        """
        from .models import IntentofallaloLogin
        
        IntentofallaloLogin.objects.create(
            username=username,
            ip_address=ip,
            user_agent=user_agent,
            razon=razon
        )
        
        logger.warning(
            f"Intento fallido de login: {username}",
            extra={
                'username': username,
                'ip': ip,
                'razon': razon,
                'evento': 'LOGIN_FALLIDO',
            }
        )
    
    @staticmethod
    def obtener_intentos_fallidos(username, horas=1):
        """
        Obtiene el número de intentos fallidos en las últimas horas
        """
        from .models import IntentofallaloLogin
        
        fecha_limite = timezone.now() - timedelta(hours=horas)
        
        return IntentofallaloLogin.objects.filter(
            username=username,
            fecha__gte=fecha_limite
        ).count()
    
    @staticmethod
    def obtener_intentos_fallidos_por_ip(ip, horas=1):
        """
        Obtiene intentos fallidos desde una IP específica
        Protección contra ataques de fuerza bruta
        """
        from .models import IntentofallaloLogin
        
        fecha_limite = timezone.now() - timedelta(hours=horas)
        
        return IntentofallaloLogin.objects.filter(
            ip_address=ip,
            fecha__gte=fecha_limite
        ).count()
    
    @staticmethod
    def esta_ip_bloqueada(ip, max_intentos=20, horas=1):
        """
        Verifica si una IP está bloqueada por múltiples intentos fallidos
        """
        intentos = AutenticacionService.obtener_intentos_fallidos_por_ip(ip, horas)
        return intentos >= max_intentos
    
    @staticmethod
    def generar_jwt_claims(usuario):
        """
        Genera claims personalizados para JWT
        """
        return {
            'usuario_id': str(usuario.id),
            'username': usuario.username,
            'rol': usuario.rol.nombre,
            'email': usuario.email,
        }
    
    @staticmethod
    def verificar_sesion_activa(usuario, max_sesiones=3):
        """
        Verifica si el usuario tiene demasiadas sesiones activas
        Previene múltiples accesos simultáneos
        """
        from .models import SesionUsuario
        
        sesiones_activas = SesionUsuario.objects.filter(
            usuario=usuario,
            activa=True,
            fecha_expiracion__gt=timezone.now()
        ).count()
        
        return sesiones_activas < max_sesiones
    
    @staticmethod
    def generar_totp_secret():
        """
        Genera un secreto para autenticación de dos factores (TOTP).
        Requiere: pip install pyotp
        """
        try:
            import pyotp
            return pyotp.random_base32()
        except ImportError:
            logger.warning('pyotp no instalado. MFA no disponible. Instale: pip install pyotp')
            return None

    @staticmethod
    def verificar_totp_code(secret, code):
        """
        Verifica un código TOTP.
        Requiere: pip install pyotp
        """
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except ImportError:
            logger.warning('pyotp no instalado. Verificación TOTP no disponible.')
            return False


class PermisosService:
    """
    Servicio de gestión de permisos y control de acceso
    Implementa Role-Based Access Control (RBAC)
    """
    
    @staticmethod
    def usuario_tiene_permiso(usuario, permiso):
        """
        Verifica si el usuario tiene un permiso específico
        """
        return usuario.rol.tiene_permiso(permiso)
    
    @staticmethod
    def usuario_puede_acceder_recurso(usuario, recurso):
        """
        Verifica si el usuario puede acceder a un recurso
        """
        # Implementar lógica de control de acceso
        return usuario.rol.nombre in ['administrador', 'psicologo']
    
    @staticmethod
    def usuario_puede_editar_usuario(usuario_actual, usuario_target):
        """
        Verifica si un usuario puede editar otro usuario
        """
        # Administrador puede editar a cualquiera
        if usuario_actual.rol.nombre == 'administrador':
            return True
        
        # Usuario solo puede editar su propio perfil
        return usuario_actual.id == usuario_target.id
    
    @staticmethod
    def usuario_puede_ver_auditoria(usuario):
        """
        Verifica si el usuario puede ver los logs de auditoría
        """
        return usuario.rol.nombre in ['administrador', 'auditoria']
    
    @staticmethod
    def usuario_es_psicologo(usuario):
        """
        Verifica si el usuario es psicólogo
        """
        return usuario.rol.nombre == 'psicologo'
    
    @staticmethod
    def usuario_es_administrador(usuario):
        """
        Verifica si el usuario es administrador
        """
        return usuario.rol.nombre == 'administrador'


class SesionService:
    """
    Servicio de gestión de sesiones
    Implementa control de sesiones seguras
    """
    
    @staticmethod
    def crear_sesion(usuario, ip, user_agent):
        """
        Crea una nueva sesión de usuario
        """
        from .models import SesionUsuario
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(usuario)
        fecha_expiracion = timezone.now() + timedelta(hours=2)
        
        sesion = SesionUsuario.objects.create(
            usuario=usuario,
            token=str(refresh.access_token),
            ip_address=ip,
            user_agent=user_agent,
            fecha_expiracion=fecha_expiracion,
        )
        
        return sesion, refresh
    
    @staticmethod
    def obtener_sesiones_activas(usuario):
        """
        Obtiene todas las sesiones activas del usuario
        """
        from .models import SesionUsuario
        
        return SesionUsuario.objects.filter(
            usuario=usuario,
            activa=True,
            fecha_expiracion__gt=timezone.now()
        )
    
    @staticmethod
    def cerrar_todas_las_sesiones(usuario):
        """
        Cierra todas las sesiones del usuario
        """
        sesiones = SesionService.obtener_sesiones_activas(usuario)
        for sesion in sesiones:
            sesion.cerrar()
        
        logger.info(
            f"Se cerraron todas las sesiones de {usuario.username}",
            extra={'usuario': usuario.username, 'evento': 'SESIONES_CERRADAS'}
        )
    
    @staticmethod
    def obtener_informacion_dispositivo(user_agent):
        """
        Extrae información del dispositivo desde User-Agent
        """
        dispositivos = {
            'Windows': 'Windows',
            'Mac': 'macOS',
            'Linux': 'Linux',
            'Android': 'Android',
            'iPhone': 'iOS',
            'iPad': 'iPad',
        }
        
        for key, value in dispositivos.items():
            if key in user_agent:
                return value
        
        return 'Desconocido'


class EncriptacionService:
    """
    Servicio de encriptación y hashing
    Implementa prácticas seguras de criptografía
    """
    
    @staticmethod
    def hashear_password(password):
        """
        Hashea una contraseña (Django lo hace automáticamente)
        """
        from django.contrib.auth.hashers import make_password
        return make_password(password)
    
    @staticmethod
    def verificar_password(password_ingresado, password_hasheado):
        """
        Verifica una contraseña contra su hash
        """
        from django.contrib.auth.hashers import check_password
        return check_password(password_ingresado, password_hasheado)
    
    @staticmethod
    def encriptar_datos(datos, clave=None):
        """
        Encripta datos sensibles.
        Requiere: pip install cryptography
        """
        try:
            from cryptography.fernet import Fernet
            if clave is None:
                clave = settings.SECRET_KEY.encode()
            clave_fernet = Fernet(clave[:44])
            return clave_fernet.encrypt(datos.encode()).decode()
        except ImportError:
            logger.warning('cryptography no instalado. Encriptación no disponible. Instale: pip install cryptography')
            return datos
        except Exception as e:
            logger.error(f'Error al encriptar datos: {e}')
            return datos

    @staticmethod
    def desencriptar_datos(datos_encriptados, clave=None):
        """
        Desencripta datos sensibles.
        Requiere: pip install cryptography
        """
        try:
            from cryptography.fernet import Fernet
            if clave is None:
                clave = settings.SECRET_KEY.encode()
            clave_fernet = Fernet(clave[:44])
            return clave_fernet.decrypt(datos_encriptados.encode()).decode()
        except ImportError:
            logger.warning('cryptography no instalado. Desencriptación no disponible.')
            return datos_encriptados
        except Exception as e:
            logger.error(f'Error al desencriptar datos: {e}')
            return datos_encriptados
