from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse  # <-- ADD THIS

from .models import Task
from .forms import TaskForm, CreateUserForm, SearchForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.conf import settings
from .rag_utils import index_documents, get_qa_chain, extract_text  # <-- add extract_text
import os
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

# ---------------- RAG VIEWS ---------------- #
@login_required(login_url='login')
def rag_upload(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        files = request.FILES.getlist("files")
        full_text = ""

        media_path = os.path.join(settings.BASE_DIR, "media")
        os.makedirs(media_path, exist_ok=True)

        for uploaded_file in files:
            file_path = os.path.join(media_path, uploaded_file.name)

            # Save file
            with open(file_path, "wb+") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Extract text from this file and append
            full_text += extract_text(file_path) + "\n"

        if not full_text.strip():
            messages.error(request, "Unable to read uploaded files.")
            return redirect("rag_upload")

        # Append to existing Chroma DB (or create new)
        db_path = os.path.join(settings.BASE_DIR, "chroma_db")
        index_documents(full_text, persist_directory=db_path)

        messages.success(request, "Documents uploaded and indexed!")
        return redirect("rag_chat")

    return render(request, "tasks/rag_upload.html")


@login_required(login_url='login')
def rag_chat(request):
    return render(request, "tasks/rag_chat.html")


@login_required(login_url='login')
def rag_query(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    import json
    data = json.loads(request.body or "{}")
    query = data.get("query", "").strip()

    if not query:
        return JsonResponse({"answer": ""})

    db_path = os.path.join(settings.BASE_DIR, "chroma_db")
    qa_chain = get_qa_chain(persist_directory=db_path)

    answer = qa_chain(query)
    return JsonResponse({"answer": str(answer)})
