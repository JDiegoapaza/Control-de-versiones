# apps/auth_app/models.py
"""
Modelos de autenticación y autorización
Implementa seguridad ISO 27001 (Confidencialidad, Integridad, Disponibilidad)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import EmailValidator
import uuid

class Rol(models.Model):
    """
    Define roles del sistema con permisos específicos
    """
    ROLE_CHOICES = (
        ('administrador', 'Administrador'),
        ('psicologo', 'Psicólogo'),
        ('director', 'Director de Centro'),
        ('auditoria', 'Auditoría'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    permisos = models.ManyToManyField(Permission, blank=True)
    
    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.CharField(max_length=100, default='sistema')
    
    class Meta:
        db_table = 'roles'
        ordering = ['nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        permissions = (
            ('ver_usuarios', 'Puede ver usuarios'),
            ('crear_usuario', 'Puede crear usuarios'),
            ('editar_usuario', 'Puede editar usuarios'),
            ('eliminar_usuario', 'Puede eliminar usuarios'),
            ('ver_auditoria', 'Puede ver auditoría'),
        )
    
    def __str__(self):
        return self.get_nombre_display()
    
    def tiene_permiso(self, permiso):
        """Verifica si el rol tiene un permiso específico"""
        return self.permisos.filter(codename=permiso).exists()


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado
    Extends Django AbstractUser con campos adicionales de seguridad
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios')
    
    # Seguridad
    activo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False)
    razon_bloqueo = models.TextField(blank=True)
    
    # Control de acceso
    ultimo_login = models.DateTimeField(null=True, blank=True)
    ultimo_login_ip = models.GenericIPAddressField(null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    fecha_desbloqueo = models.DateTimeField(null=True, blank=True)
    
    # Cambio de contraseña
    debe_cambiar_password = models.BooleanField(default=False)
    fecha_cambio_password = models.DateTimeField(auto_now=True)
    
    # Datos adicionales
    telefono = models.CharField(max_length=20, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)  # Para psicólogos
    centro_penitenciario = models.CharField(max_length=200, blank=True)
    
    # Auditoría
    creado_por = models.CharField(max_length=100, default='sistema')
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'rol_id']
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def puede_acceder_recurso(self, recurso):
        """Verifica si el usuario puede acceder a un recurso específico"""
        return self.rol.tiene_permiso(recurso)
    
    def desbloquear(self):
        """Desbloquea el usuario después del tiempo de espera"""
        if self.fecha_desbloqueo and timezone.now() >= self.fecha_desbloqueo:
            self.bloqueado = False
            self.intentos_fallidos = 0
            self.fecha_desbloqueo = None
            self.razon_bloqueo = ""
            self.save()
            return True
        return False
    
    def registrar_intento_fallido(self):
        """Registra un intento de login fallido"""
        self.intentos_fallidos += 1
        
        # Bloquear si excede máximo de intentos (5 intentos, 15 min)
        if self.intentos_fallidos >= 5:
            self.bloqueado = True
            self.fecha_desbloqueo = timezone.now() + timezone.timedelta(minutes=15)
            self.razon_bloqueo = "Múltiples intentos fallidos de login"
        
        self.save()
    
    def limpiar_intentos_fallidos(self):
        """Limpia los intentos fallidos después de login exitoso"""
        self.intentos_fallidos = 0
        self.bloqueado = False
        self.fecha_desbloqueo = None
        self.razon_bloqueo = ""
        self.save()


class TokenRefresh(models.Model):
    """
    Mantiene un registro de tokens para gestión de sesiones
    Permite revocación de tokens
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tokens')
    token_jti = models.CharField(max_length=500, unique=True)  # JWT ID
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    fecha_revocacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'token_refresh'
        ordering = ['-fecha_creacion']
    
    def revocar(self):
        """Revoca el token"""
        self.activo = False
        self.fecha_revocacion = timezone.now()
        self.save()


class SesionUsuario(models.Model):
    """
    Rastrea sesiones activas del usuario
    Implementa multi-device security
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones')
    token = models.CharField(max_length=500)
    dispositivo = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'sesiones_usuario'
        ordering = ['-fecha_creacion']
    
    def cerrar(self):
        """Cierra la sesión"""
        self.activa = False
        self.fecha_cierre = timezone.now()
        self.save()
    
    def esta_activa(self):
        """Verifica si la sesión aún es válida"""
        return self.activa and timezone.now() < self.fecha_expiracion


class IntentofallaloLogin(models.Model):
    """
    Registra intentos fallidos de login para auditoría
    Implementa protección contra fuerza bruta
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    razon = models.CharField(max_length=200)  # "contraseña incorrecta", "usuario no existe", etc.
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'intentos_fallidos_login'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['username', 'fecha']),
            models.Index(fields=['ip_address', 'fecha']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.ip_address} - {self.fecha}"


class RecuperacionPassword(models.Model):
    """
    Gestiona tokens de recuperación de contraseña
    Implementa seguridad en reset de passwords
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='recuperaciones')
    token = models.CharField(max_length=200, unique=True)
    usado = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    fecha_uso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'recuperacion_password'
        ordering = ['-fecha_creacion']
    
    def esta_vigente(self):
        """Verifica si el token aún es válido"""
        return not self.usado and timezone.now() < self.fecha_expiracion
    
    def usar(self):
        """Marca el token como usado"""
        self.usado = True
        self.fecha_uso = timezone.now()
        self.save()
