# apps/dashboard_app/serializers.py
from rest_framework import serializers
from .models import ConfiguracionDashboard


class ConfiguracionDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionDashboard
        fields = '__all__'
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
