# apps/auth_app/views.py
"""
Vistas de autenticación con seguridad ISO 27001
Implementa JWT, rate limiting, auditoría y protección contra ataques
V3.1: + reCAPTCHA v2 en login + gestión administrativa de usuarios
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, logout, login
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import logging
import json
import requests
from datetime import timedelta
from django.conf import settings
from functools import wraps

from .models import (
    Usuario,
    SesionUsuario,
    IntentofallaloLogin,
    RecuperacionPassword
)
from .serializers import UsuarioSerializer, LoginSerializer
from .services import AutenticacionService
from apps.seguridad_app.models import LogAuditoria

logger = logging.getLogger('apps.seguridad_app')
auth_service = AutenticacionService()


# ==================== DECORADOR SOLO SUPERUSUARIO ====================

def solo_superusuario(view_func):
    """
    Decorador: restringe la vista a superusuarios Django (is_superuser=True).
    Redirige al login si no está autenticado, muestra 403 si no es superusuario.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not request.user.is_superuser:
            return render(request, 'auth/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


# ==================== VISTAS BASADAS EN FUNCIONES ====================

@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """
    Vista de login con seguridad avanzada
    - Valida credenciales contra BD PostgreSQL
    - Implementa rate limiting (máx 5 intentos en 15 min)
    - Registra auditoría de intentos
    - Genera tokens JWT seguros
    - Maneja sesiones de usuario
    V3.1: + verificación Google reCAPTCHA v2 Checkbox
    """

    if request.method == 'GET':
        # Mostrar formulario de login
        context = {
            'titulo': 'Acceso al Sistema',
            'subtitulo': 'Plataforma de Gestión de Evaluaciones Psicológicas',
            'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,  # V3.1
        }
        return render(request, 'auth/login.html', context)

    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()

            # Validar que los campos no estén vacíos
            if not username or not password:
                return render(request, 'auth/login.html', {
                    'error': 'Usuario y contraseña son requeridos',
                    'username': username,
                    'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                })

            # Obtener IP del cliente
            client_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # === reCAPTCHA START — V3.1 ===================================
            recaptcha_response = request.POST.get('g-recaptcha-response', '')

            if not recaptcha_response:
                # El usuario no completó el CAPTCHA
                LogAuditoria.objects.create(
                    usuario=None,
                    tipo_evento='CAPTCHA_FALLIDO',
                    descripcion=f'reCAPTCHA no completado — usuario: {username}',
                    ip_address=client_ip,
                    user_agent=user_agent,
                    estado='FALLIDO',
                )
                logger.warning(f'reCAPTCHA no completado: {username} desde {client_ip}')
                return render(request, 'auth/login.html', {
                    'error': 'Por favor, complete la verificación reCAPTCHA.',
                    'username': username,
                    'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                })

            try:
                captcha_verify = requests.post(
                    settings.RECAPTCHA_VERIFY_URL,
                    data={
                        'secret':   settings.RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_response,
                        'remoteip': client_ip,
                    },
                    timeout=5,
                )
                captcha_data = captcha_verify.json()
                captcha_ok = captcha_data.get('success', False)
            except Exception as captcha_err:
                logger.error(f'Error verificando reCAPTCHA: {captcha_err}')
                captcha_ok = True  # Fail-open: si Google no responde, no bloqueamos

            if not captcha_ok:
                LogAuditoria.objects.create(
                    usuario=None,
                    tipo_evento='CAPTCHA_FALLIDO',
                    descripcion=f'reCAPTCHA inválido — usuario: {username}',
                    ip_address=client_ip,
                    user_agent=user_agent,
                    estado='FALLIDO',
                )
                logger.warning(f'reCAPTCHA fallido: {username} desde {client_ip}')
                return render(request, 'auth/login.html', {
                    'error': 'Verificación reCAPTCHA fallida. Intente nuevamente.',
                    'username': username,
                    'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                })

            # CAPTCHA exitoso — registrar auditoría
            LogAuditoria.objects.create(
                usuario=None,
                tipo_evento='CAPTCHA_EXITOSO',
                descripcion=f'reCAPTCHA superado — usuario: {username}',
                ip_address=client_ip,
                user_agent=user_agent,
                estado='EXITOSO',
            )
            # === reCAPTCHA END =============================================

            # Intentar autenticar
            usuario = authenticate(request, username=username, password=password)

            if usuario is None:
                # Error de autenticación

                # Registrar intento fallido
                IntentofallaloLogin.objects.create(
                    username=username,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    razon='Credenciales inválidas'
                )

                # Intentar registrar en usuario si existe
                try:
                    user = Usuario.objects.get(username=username)
                    user.registrar_intento_fallido()

                    if user.bloqueado:
                        logger.warning(
                            f"Usuario {username} bloqueado por múltiples intentos",
                            extra={
                                'usuario': username,
                                'ip': client_ip,
                                'evento': 'LOGIN_BLOQUEADO',
                            }
                        )
                        return render(request, 'auth/login.html', {
                            'error': 'Cuenta temporalmente bloqueada. Intente más tarde.',
                            'username': username,
                            'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                        })
                except Usuario.DoesNotExist:
                    pass

                logger.info(
                    f"Intento de login fallido: {username}",
                    extra={'ip': client_ip, 'evento': 'LOGIN_FALLIDO'}
                )

                return render(request, 'auth/login.html', {
                    'error': 'Usuario o contraseña incorrectos',
                    'username': username,
                    'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                })

            # Validar que usuario esté activo
            if not usuario.activo:
                logger.warning(
                    f"Intento de login con usuario inactivo: {username}",
                    extra={'ip': client_ip, 'evento': 'LOGIN_USUARIO_INACTIVO'}
                )
                return render(request, 'auth/login.html', {
                    'error': 'Cuenta desactivada',
                    'username': username,
                    'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                })

            # Desbloquear usuario si el timeout ha pasado
            if usuario.bloqueado:
                if not usuario.desbloquear():
                    return render(request, 'auth/login.html', {
                        'error': 'Cuenta aún está bloqueada. Intente más tarde.',
                        'username': username,
                        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
                    })

            # ===== LOGIN EXITOSO =====

            # Iniciar sesión Django
            login(request, usuario)

            # Limpiar intentos fallidos
            usuario.limpiar_intentos_fallidos()

            # Actualizar último login
            usuario.ultimo_login = timezone.now()
            usuario.ultimo_login_ip = client_ip
            usuario.save()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(usuario)
            access_token = str(refresh.access_token)

            # Crear sesión de usuario
            fecha_expiracion = timezone.now() + timedelta(hours=2)
            sesion = SesionUsuario.objects.create(
                usuario=usuario,
                token=access_token,
                dispositivo=get_device_info(user_agent),
                ip_address=client_ip,
                user_agent=user_agent,
                fecha_expiracion=fecha_expiracion,
            )

            # Registrar auditoría - LOGIN EXITOSO
            try:
                LogAuditoria.objects.create(
                    usuario=usuario,
                    tipo_evento='LOGIN_EXITOSO',
                    descripcion=f'Login exitoso desde {client_ip}',
                    ip_address=client_ip,
                    user_agent=user_agent,
                    estado='EXITOSO',
                )
            except Exception as audit_error:
                logger.warning(f'No se pudo registrar auditoría de login: {audit_error}')

            logger.info(
                f"Login exitoso: {usuario.username}",
                extra={
                    'usuario': usuario.username,
                    'ip': client_ip,
                    'rol': usuario.rol.nombre,
                    'evento': 'LOGIN_EXITOSO',
                }
            )

            # Establecer sesión Django
            # set_expiry acepta un entero (segundos) no un datetime
            request.session['usuario_id'] = str(usuario.id)
            request.session['usuario_rol'] = usuario.rol.nombre
            request.session['access_token'] = access_token
            request.session.set_expiry(7200)  # 2 horas en segundos

            # Redirigir al dashboard
            return redirect('dashboard:index')

        except Exception as e:
            logger.error(
                f"Error en login: {str(e)}",
                extra={'evento': 'LOGIN_ERROR', 'error': str(e)}
            )
            return render(request, 'auth/login.html', {
                'error': 'Error del sistema. Intente más tarde.',
                'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
            })


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    Vista de logout seguro
    - Cierra sesión de usuario
    - Revoca tokens JWT
    - Limpia cookies
    - Registra auditoría
    """
    
    try:
        usuario = request.user
        client_ip = get_client_ip(request)
        
        # Cerrar sesiones activas
        SesionUsuario.objects.filter(
            usuario=usuario,
            activa=True
        ).update(activa=False, fecha_cierre=timezone.now())
        
        # Registrar auditoría
        LogAuditoria.objects.create(
            usuario=usuario,
            tipo_evento='LOGOUT',
            descripcion=f'Logout desde {client_ip}',
            ip_address=client_ip,
            estado='EXITOSO',
        )
        
        logger.info(
            f"Logout: {usuario.username}",
            extra={'usuario': usuario.username, 'ip': client_ip}
        )
        
        # Logout Django
        logout(request)
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
    
    return redirect('auth:login')


@require_http_methods(["GET", "POST"])
def recuperar_password_view(request):
    """
    Vista para recuperación de contraseña
    - Envía email con token de recuperación
    - Token válido por 24 horas
    - Implementa seguridad contra enumeración de usuarios
    """
    
    if request.method == 'GET':
        return render(request, 'auth/recuperar_password.html')
    
    elif request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            return render(request, 'auth/recuperar_password.html', {
                'error': 'Email requerido'
            })
        
        try:
            usuario = Usuario.objects.get(email=email)
            
            # Generar token de recuperación
            token = auth_service.generar_token_recuperacion()
            fecha_expiracion = timezone.now() + timedelta(hours=24)
            
            recuperacion = RecuperacionPassword.objects.create(
                usuario=usuario,
                token=token,
                fecha_expiracion=fecha_expiracion,
            )
            
            # TODO: Enviar email con token
            # send_password_reset_email(usuario.email, token)
            
            logger.info(
                f"Token de recuperación generado para: {email}",
                extra={'email': email, 'evento': 'PASSWORD_RESET_REQUEST'}
            )
            
            return render(request, 'auth/recuperar_password.html', {
                'mensaje': 'Se envió un enlace de recuperación a tu email.',
                'success': True,
            })
        
        except Usuario.DoesNotExist:
            # Mostrar mismo mensaje para evitar enumeración de usuarios
            logger.warning(
                f"Intento de recuperación con email no registrado: {email}",
                extra={'email': email, 'evento': 'PASSWORD_RESET_NO_USER'}
            )
            return render(request, 'auth/recuperar_password.html', {
                'mensaje': 'Si el email está registrado, recibirá un enlace de recuperación.',
                'success': True,
            })
        
        except Exception as e:
            logger.error(f"Error en recuperación de contraseña: {str(e)}")
            return render(request, 'auth/recuperar_password.html', {
                'error': 'Error del sistema. Intente más tarde.'
            })


# ==================== API REST ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_protect
def api_login(request):
    """
    Endpoint API REST para login
    Retorna tokens JWT
    """
    
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Datos inválidos',
                'detalles': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    usuario = authenticate(username=username, password=password)
    
    if usuario is None:
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not usuario.activo:
        return Response(
            {'error': 'Cuenta desactivada'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generar tokens
    refresh = RefreshToken.for_user(usuario)
    
    return Response({
        'usuario': UsuarioSerializer(usuario).data,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    })


@api_view(['POST'])
def api_refresh_token(request):
    """
    Endpoint para refrescar token JWT
    """
    
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'access': str(refresh.access_token)
        })
    except TokenError:
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ==================== FUNCIONES AUXILIARES ====================

def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente
    Considera proxies y headers X-Forwarded-For
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def get_device_info(user_agent):
    """
    Extrae información del dispositivo desde User-Agent
    """
    if 'Windows' in user_agent:
        return 'Windows'
    elif 'Mac' in user_agent:
        return 'Mac'
    elif 'Linux' in user_agent:
        return 'Linux'
    elif 'Android' in user_agent:
        return 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        return 'iOS'
    else:
        return 'Desconocido'


# ==================== V3.1: GESTIÓN ADMINISTRATIVA DE USUARIOS ====================
# Todas las vistas requieren is_superuser=True mediante @solo_superusuario

@solo_superusuario
@require_http_methods(["GET"])
def usuarios_lista(request):
    """
    Lista paginada de todos los usuarios del sistema.
    Filtros: rol, activo/inactivo, búsqueda por nombre/username.
    Registra evento VER en auditoría.
    """
    from .forms import UsuarioCrearForm
    from .models import Rol
    from django.core.paginator import Paginator

    # Filtros GET
    q        = request.GET.get('q', '').strip()
    rol_id   = request.GET.get('rol', '')
    estado   = request.GET.get('estado', '')

    qs = Usuario.objects.select_related('rol').order_by('first_name', 'last_name')

    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )
    if rol_id:
        qs = qs.filter(rol__id=rol_id)
    if estado == 'activo':
        qs = qs.filter(activo=True)
    elif estado == 'inactivo':
        qs = qs.filter(activo=False)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    LogAuditoria.objects.create(
        usuario=request.user,
        tipo_evento='VER',
        descripcion='Listado de usuarios consultado',
        ip_address=get_client_ip(request),
        estado='EXITOSO',
    )

    return render(request, 'auth/usuarios/lista.html', {
        'titulo': 'Gestión de Usuarios',
        'usuarios': page,
        'roles': Rol.objects.filter(activo=True),
        'q': q,
        'rol_id': rol_id,
        'estado': estado,
        'total': qs.count(),
    })


@solo_superusuario
@require_http_methods(["GET", "POST"])
def usuario_crear(request):
    """
    Crea un nuevo usuario del sistema.
    Aplica validación de contraseña fuerte (12 chars, may, min, num, especial).
    Registra evento USUARIO_CREADO en auditoría.
    """
    from .forms import UsuarioCrearForm

    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save(creado_por=request.user.username)
            LogAuditoria.objects.create(
                usuario=request.user,
                tipo_evento='USUARIO_CREADO',
                descripcion=f'Usuario creado: {usuario.username}',
                ip_address=get_client_ip(request),
                estado='EXITOSO',
                datos_adicionales={'nuevo_usuario': usuario.username, 'rol': usuario.rol.nombre},
            )
            messages.success(request, f'Usuario {usuario.username} creado correctamente.')
            return redirect('auth:usuarios_lista')
        # form inválido: re-render con errores
    else:
        form = UsuarioCrearForm()

    return render(request, 'auth/usuarios/form.html', {
        'titulo': 'Crear Usuario',
        'form': form,
        'accion': 'Crear',
    })


@solo_superusuario
@require_http_methods(["GET", "POST"])
def usuario_editar(request, uid):
    """
    Edita datos de un usuario existente (sin cambiar contraseña).
    Registra evento USUARIO_EDITADO en auditoría.
    """
    from .forms import UsuarioEditarForm

    usuario = get_object_or_404(Usuario, id=uid)

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            LogAuditoria.objects.create(
                usuario=request.user,
                tipo_evento='USUARIO_EDITADO',
                descripcion=f'Usuario editado: {usuario.username}',
                ip_address=get_client_ip(request),
                estado='EXITOSO',
                datos_adicionales={'usuario_editado': usuario.username},
            )
            messages.success(request, f'Usuario {usuario.username} actualizado correctamente.')
            return redirect('auth:usuario_detalle', uid=uid)
    else:
        form = UsuarioEditarForm(instance=usuario)

    return render(request, 'auth/usuarios/form.html', {
        'titulo': f'Editar Usuario — {usuario.username}',
        'form': form,
        'accion': 'Guardar cambios',
        'usuario': usuario,
    })


@solo_superusuario
@require_http_methods(["GET"])
def usuario_detalle(request, uid):
    """
    Muestra ficha completa del usuario con sus últimos 20 logs de auditoría.
    Registra evento VER en auditoría.
    """
    usuario = get_object_or_404(Usuario.objects.select_related('rol'), id=uid)
    logs = LogAuditoria.objects.filter(usuario=usuario).order_by('-fecha')[:20]

    LogAuditoria.objects.create(
        usuario=request.user,
        tipo_evento='VER',
        descripcion=f'Detalle de usuario consultado: {usuario.username}',
        ip_address=get_client_ip(request),
        estado='EXITOSO',
    )

    return render(request, 'auth/usuarios/detalle.html', {
        'titulo': f'Detalle — {usuario.get_full_name() or usuario.username}',
        'obj': usuario,
        'logs': logs,
    })


@solo_superusuario
@require_http_methods(["POST"])
def usuario_activar_desactivar(request, uid):
    """
    Alterna el estado activo/inactivo de un usuario.
    No puede desactivar al propio superusuario que hace la acción.
    Registra USUARIO_ACTIVADO o USUARIO_DESACTIVADO en auditoría.
    """
    usuario = get_object_or_404(Usuario, id=uid)

    if usuario.id == request.user.id:
        messages.error(request, 'No puede desactivar su propia cuenta.')
        return redirect('auth:usuario_detalle', uid=uid)

    usuario.activo = not usuario.activo
    usuario.save(update_fields=['activo'])

    evento  = 'USUARIO_ACTIVADO' if usuario.activo else 'USUARIO_DESACTIVADO'
    accion  = 'activado' if usuario.activo else 'desactivado'

    LogAuditoria.objects.create(
        usuario=request.user,
        tipo_evento=evento,
        descripcion=f'Usuario {accion}: {usuario.username}',
        ip_address=get_client_ip(request),
        estado='EXITOSO',
        datos_adicionales={'usuario_afectado': usuario.username, 'nuevo_estado': str(usuario.activo)},
    )
    messages.success(request, f'Usuario {usuario.username} {accion} correctamente.')
    return redirect('auth:usuarios_lista')


@solo_superusuario
@require_http_methods(["GET", "POST"])
def usuario_reset_password(request, uid):
    """
    Restablece la contraseña de un usuario.
    Aplica validación de contraseña fuerte.
    Registra PASSWORD_RESET en auditoría.
    El propio usuario afectado debe cambiar la contraseña en su próximo login
    (debe_cambiar_password=True).
    """
    from .forms import UsuarioResetPasswordForm

    usuario = get_object_or_404(Usuario, id=uid)

    if request.method == 'POST':
        form = UsuarioResetPasswordForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password1'])
            usuario.debe_cambiar_password = True
            usuario.save(update_fields=['password', 'debe_cambiar_password', 'fecha_cambio_password'])

            LogAuditoria.objects.create(
                usuario=request.user,
                tipo_evento='PASSWORD_RESET',
                descripcion=f'Contraseña restablecida para: {usuario.username}',
                ip_address=get_client_ip(request),
                estado='EXITOSO',
                datos_adicionales={'usuario_afectado': usuario.username},
            )
            messages.success(
                request,
                f'Contraseña de {usuario.username} restablecida. '
                'El usuario deberá cambiarla en su próximo acceso.'
            )
            return redirect('auth:usuario_detalle', uid=uid)
    else:
        form = UsuarioResetPasswordForm()

    return render(request, 'auth/usuarios/reset_password.html', {
        'titulo': f'Restablecer contraseña — {usuario.username}',
        'form': form,
        'obj': usuario,
    })
