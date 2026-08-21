# apps/reportes_app/serializers.py
from rest_framework import serializers
from .models import Reporte


class ReporteSerializer(serializers.ModelSerializer):
    tipo_display   = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    generado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = Reporte
        fields = [
            'id', 'titulo', 'tipo', 'tipo_display', 'formato',
            'estado', 'estado_display', 'generado_por', 'generado_por_nombre',
            'parametros', 'error_mensaje',
            'fecha_solicitud', 'fecha_generacion',
        ]
        read_only_fields = ['id', 'fecha_solicitud', 'fecha_generacion', 'estado']

    def get_generado_por_nombre(self, obj):
        if obj.generado_por:
            return str(obj.generado_por)
        return None
