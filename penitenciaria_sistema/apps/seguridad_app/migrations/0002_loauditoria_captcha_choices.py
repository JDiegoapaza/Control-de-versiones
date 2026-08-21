# apps/seguridad_app/migrations/0002_loauditoria_captcha_choices.py
"""
Migración SGEP V3.1 — Agrega CAPTCHA_EXITOSO y CAPTCHA_FALLIDO a TIPO_EVENTO_CHOICES.
Operación segura en SQLite: los choices son validación Python, no constraints de BD.
No altera columnas ni tablas existentes.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seguridad_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logauditoria',
            name='tipo_evento',
            field=models.CharField(
                choices=[
                    ('LOGIN_EXITOSO',   'Login exitoso'),
                    ('LOGIN_FALLIDO',   'Login fallido'),
                    ('LOGIN_BLOQUEADO', 'Login bloqueado'),
                    ('LOGOUT',         'Logout'),
                    ('CAPTCHA_EXITOSO', 'CAPTCHA verificado'),       # NUEVO V3.1
                    ('CAPTCHA_FALLIDO', 'CAPTCHA fallido'),          # NUEVO V3.1
                    ('CREAR',          'Creación de registro'),
                    ('EDITAR',         'Edición de registro'),
                    ('ELIMINAR',       'Eliminación de registro'),
                    ('VER',            'Visualización de registro'),
                    ('EXPORTAR',       'Exportación de datos'),
                    ('ERROR',          'Error del sistema'),
                    ('USUARIO_CREADO',     'Usuario creado'),        # NUEVO V3.1
                    ('USUARIO_EDITADO',    'Usuario editado'),       # NUEVO V3.1
                    ('USUARIO_ACTIVADO',   'Usuario activado'),      # NUEVO V3.1
                    ('USUARIO_DESACTIVADO','Usuario desactivado'),   # NUEVO V3.1
                    ('PASSWORD_RESET',     'Contraseña restablecida'),# NUEVO V3.1
                ],
                max_length=30,
                verbose_name='Tipo de evento',
            ),
        ),
    ]
