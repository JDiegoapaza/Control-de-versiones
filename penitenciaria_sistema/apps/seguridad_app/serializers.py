# apps/seguridad_app/serializers.py
from rest_framework import serializers
from .models import LogAuditoria, ConfiguracionSeguridad


class LogAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAuditoria
        fields = '__all__'
        read_only_fields = ['id', 'fecha']


class ConfiguracionSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionSeguridad
        fields = '__all__'
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
