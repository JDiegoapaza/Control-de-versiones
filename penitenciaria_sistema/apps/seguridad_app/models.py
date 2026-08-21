# apps/seguridad_app/models.py
"""
Modelos de auditoría y seguridad del sistema.
Registra eventos, accesos y acciones de usuarios (ISO 27001).
"""

import uuid
from django.db import models
from django.utils import timezone


class LogAuditoria(models.Model):
    """
    Registro de auditoría de acciones en el sistema.
    Implementa trazabilidad completa (ISO 27001).
    """

    TIPO_EVENTO_CHOICES = [
        ('LOGIN_EXITOSO',      'Login exitoso'),
        ('LOGIN_FALLIDO',      'Login fallido'),
        ('LOGIN_BLOQUEADO',    'Login bloqueado'),
        ('LOGOUT',             'Logout'),
        # ── V3.1: reCAPTCHA ──────────────────────────────────
        ('CAPTCHA_EXITOSO',    'CAPTCHA verificado'),
        ('CAPTCHA_FALLIDO',    'CAPTCHA fallido'),
        # ── V3.1: gestión de usuarios ─────────────────────────
        ('USUARIO_CREADO',     'Usuario creado'),
        ('USUARIO_EDITADO',    'Usuario editado'),
        ('USUARIO_ACTIVADO',   'Usuario activado'),
        ('USUARIO_DESACTIVADO','Usuario desactivado'),
        ('PASSWORD_RESET',     'Contraseña restablecida'),
        # ── Eventos generales ─────────────────────────────────
        ('CREAR',              'Creación de registro'),
        ('EDITAR',             'Edición de registro'),
        ('ELIMINAR',           'Eliminación de registro'),
        ('VER',                'Visualización de registro'),
        ('EXPORTAR',           'Exportación de datos'),
        ('ERROR',              'Error del sistema'),
    ]

    ESTADO_CHOICES = [
        ('EXITOSO', 'Exitoso'),
        ('FALLIDO', 'Fallido'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='logs_auditoria',
        verbose_name='Usuario'
    )
    tipo_evento = models.CharField(max_length=30, choices=TIPO_EVENTO_CHOICES, verbose_name='Tipo de evento')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    accion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Acción')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='EXITOSO', verbose_name='Estado')
    datos_adicionales = models.JSONField(default=dict, blank=True, verbose_name='Datos adicionales')

    # Timestamp
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')

    class Meta:
        db_table = 'log_auditoria'
        verbose_name = 'Log de auditoría'
        verbose_name_plural = 'Logs de auditoría'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['tipo_evento', 'fecha']),
            models.Index(fields=['usuario', 'fecha']),
            models.Index(fields=['ip_address', 'fecha']),
        ]

    def __str__(self) -> str:
        usuario_str = str(self.usuario) if self.usuario else 'Anónimo'
        return f"{self.tipo_evento} - {usuario_str} - {self.fecha}"


class ConfiguracionSeguridad(models.Model):
    """
    Configuración de parámetros de seguridad del sistema.
    Permite ajustar políticas sin reiniciar el servidor.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clave = models.CharField(max_length=100, unique=True, verbose_name='Clave')
    valor = models.TextField(verbose_name='Valor')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_seguridad'
        verbose_name = 'Configuración de seguridad'
        verbose_name_plural = 'Configuraciones de seguridad'
        ordering = ['clave']

    def __str__(self) -> str:
        return f"{self.clave}: {self.valor[:50]}"
