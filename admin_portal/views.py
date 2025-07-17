from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User, Group, Permission
from admin_portal.models import LecturerCode
from django.utils import timezone
import secrets
from django.views.decorators.csrf import csrf_protect

# Create your views here.

def admin_login_page(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_superuser or user.is_staff):
            login(request, user)
            return redirect('/admin_portal/dashboard/')
        else:
            error = 'Invalid credentials or not an admin.'
    return render(request, 'admin_portal/login.html', {'error': error})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@csrf_protect
def generate_code(request):
    if request.method == 'POST':
        lecturer_username = request.POST.get('lecturer_username')
        duration = int(request.POST.get('duration', 1))
        try:
            lecturer = User.objects.get(username=lecturer_username)
            code = secrets.token_urlsafe(8)
            now = timezone.now()
            expires = now + timezone.timedelta(hours=duration)
            LecturerCode.objects.create(code=code, lecturer_user=lecturer, is_active=True, created_at=now, expires_at=expires)
        except User.DoesNotExist:
            pass  # Optionally, handle error with messages framework
    return redirect('admin_portal:admin_dashboard_page')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@csrf_protect
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        disable_password = request.POST.get('disable_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        is_active = bool(request.POST.get('is_active'))
        is_staff = bool(request.POST.get('is_staff'))
        is_superuser = bool(request.POST.get('is_superuser'))
        group_ids = request.POST.getlist('groups')
        perm_ids = request.POST.getlist('user_permissions')
        from django.contrib.auth.models import Group, Permission
        if User.objects.filter(username=username).exists():
            # Optionally, add error message handling
            return redirect('admin_portal:admin_dashboard_page')
        user = User.objects.create_user(username=username, email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        if not disable_password and password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        # Assign groups
        if group_ids:
            user.groups.set(Group.objects.filter(id__in=group_ids))
        # Assign permissions
        if perm_ids:
            user.user_permissions.set(Permission.objects.filter(id__in=perm_ids))
        return redirect('admin_portal:admin_dashboard_page')
    return redirect('admin_portal:admin_dashboard_page')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_dashboard_page(request):
    message = None
    error = None
    from django.db.models import Q
    # Add new admin
    if request.method == 'POST' and 'add_admin' in request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        if User.objects.filter(username=username).exists():
            error = 'Username already exists.'
        else:
            user = User.objects.create_user(username=username, password=password, email=email, is_staff=True, is_superuser=True)
            message = f'Admin {username} created.'
    # Generate lecturer code
    if request.method == 'POST' and 'generate_code' in request.POST:
        lecturer_username = request.POST.get('lecturer_username')
        duration = int(request.POST.get('duration', 1))
        try:
            lecturer = User.objects.get(username=lecturer_username)
            code = secrets.token_urlsafe(8)
            now = timezone.now()
            expires = now + timezone.timedelta(hours=duration)
            LecturerCode.objects.create(code=code, lecturer_user=lecturer, is_active=True, created_at=now, expires_at=expires)
            message = f'Code generated for {lecturer_username}.'
        except User.DoesNotExist:
            error = 'Lecturer not found.'
    codes = LecturerCode.objects.select_related('lecturer_user').order_by('-created_at')
    groups = Group.objects.all().order_by('name')
    permissions = Permission.objects.all().order_by('name')
    users = User.objects.all().order_by('username')
    return render(request, 'admin_portal/dashboard.html', {
        'codes': codes,
        'groups': groups,
        'permissions': permissions,
        'users': users,
        'message': message,
        'error': error
    })
