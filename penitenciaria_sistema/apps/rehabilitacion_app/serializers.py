# apps/rehabilitacion_app/serializers.py
from rest_framework import serializers
from .models import ProgramaRehabilitacion, Rehabilitacion


class ProgramaRehabilitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaRehabilitacion
        fields = '__all__'
        read_only_fields = ['id', 'creado_en', 'actualizado_en']


class RehabilitacionSerializer(serializers.ModelSerializer):
    programa_nombre = serializers.CharField(source='programa.nombre', read_only=True)

    class Meta:
        model = Rehabilitacion
        fields = '__all__'
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
