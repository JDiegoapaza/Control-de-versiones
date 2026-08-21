# apps/evaluaciones_app/serializers.py
from rest_framework import serializers
from .models import Evaluacion


class EvaluacionSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    nivel_riesgo_display = serializers.CharField(source='get_nivel_riesgo_display', read_only=True)

    class Meta:
        model = Evaluacion
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'fecha_completada']
