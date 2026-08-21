# apps/internos_app/models.py
"""
Modelos de gestión de internos del centro penitenciario.
Registra datos personales, estado legal y seguimiento.
"""

import uuid
from django.db import models
from django.utils import timezone


class Interno(models.Model):
    """
    Representa a una persona privada de libertad en el sistema.
    """

    ESTADO_CHOICES = [
        ('procesado', 'Procesado'),
        ('condenado', 'Condenado'),
        ('liberado', 'Liberado'),
        ('traslado', 'Trasladado'),
    ]

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cédula de identidad')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default='M', verbose_name='Sexo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='procesado', verbose_name='Estado')
    delito = models.CharField(max_length=255, blank=True, verbose_name='Delito imputado')
    fecha_ingreso = models.DateTimeField(default=timezone.now, verbose_name='Fecha de ingreso')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    fecha_liberacion_prevista = models.DateField(null=True, blank=True, verbose_name='Fecha de liberación prevista')
    centro_penitenciario = models.CharField(max_length=200, blank=True, verbose_name='Centro penitenciario')
    celda = models.CharField(max_length=20, blank=True, verbose_name='Celda')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    # Soft delete
    activo = models.BooleanField(default=True, verbose_name='Activo')
    eliminado_en = models.DateTimeField(null=True, blank=True, verbose_name='Eliminado en')

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'internos'
        verbose_name = 'Interno'
        verbose_name_plural = 'Internos'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['estado']),
        ]

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre} ({self.cedula})"

    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def soft_delete(self) -> None:
        """Elimina lógicamente el registro."""
        self.activo = False
        self.eliminado_en = timezone.now()
        self.save()
