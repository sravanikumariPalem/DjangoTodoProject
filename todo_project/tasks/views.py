from django.shortcuts import render, redirect, get_object_or_404
from .models import Task
from .forms import TaskForm, CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SearchForm
# Create your views here.

@login_required(login_url='login')
def index(request):
    tasks = Task.objects.filter(user=request.user)  # show only user-specific tasks
    form = TaskForm(user=request.user)
    search_form = SearchForm(request.GET or None)

    if search_form.is_valid() and search_form.cleaned_data['search']:
        search_query = search_form.cleaned_data['search']
        tasks = tasks.filter(title__icontains=search_query)
    search_form=SearchForm()
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task added successfully!')
            return redirect('/')
        else:
            for error in form.errors.get('title', []):
                messages.warning(request, error)
        form = TaskForm(user=request.user)  # reset form after POST
    context = {'tasks': tasks, 'form': form, 'search_form': search_form}
    return render(request, 'tasks/index.html', context)

def updateTask(request, pk):
    task = get_object_or_404(Task, id=pk)
    form = TaskForm(instance=task)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('/')
    context = {'form': form}
    return render(request, 'tasks/update_task.html', context)

def deleteTask(request, pk):
    task = get_object_or_404(Task, id=pk)
    if request.method == 'POST':
        task.delete()
        return redirect('/')
    context = {'task': task}
    return render(request, 'tasks/delete_task.html', context)

def registerPage(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user)
                return redirect('login')
        context = {'form': form}
        return render(request, 'tasks/register.html', context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.info(request, 'Username OR password is incorrect')
        context = {}
        return render(request, 'tasks/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

def forgotPassword(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        # Here you would typically handle password reset logic
        new_password=request.POST.get('new_password')
        confirm_password=request.POST.get('confirm_password')

        try:
            user=User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'tasks/forgot_password.html', {'error': 'Username not found'})
        if new_password != confirm_password:
            return render(request, 'tasks/forgot_password.html', {'error': 'Passwords do not match','username':username})
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Password reset successful. Please log in with your new password.')
        return redirect('login')
    return render(request, 'tasks/forgot_password.html')