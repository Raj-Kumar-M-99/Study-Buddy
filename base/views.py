from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

# Create your views here.
def loginPage(request): 
    page = 'login'
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request,'User does not exists!')
            
        user = authenticate(request,email=email,password=password)
        
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Username or password does not exist!!')
    
    context = {"page":page}
    return render(request,'base/login_register.html',context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def register(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"An error occured during registration")
            
    context = {"form":form}
    return render(request,'base/login_register.html',context)

    
def home(request):
    query = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=query) |
        Q(name__icontains=query)|
        Q(description__icontains=query)
        )
    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=query))
    
    context = {"rooms":rooms,"topics":topics,
               "room_count":room_count,"room_messages":room_messages}
    return render(request,"base/home.html",context)


def room(request,pk):
    rooms = Room.objects.get(id=pk)
    room_messages = rooms.message_set.all().order_by('-createdDate')
    participants = rooms.participants.all()
    
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = rooms,
            body = request.POST.get('body')
        )
        rooms.participants.add(request.user)
        return redirect('room',pk=rooms.id )
    context = {"rooms":rooms,"room_messages":room_messages,'participants':participants}
    print("Logging:",rooms.host.id)
    return render(request,"base/room.html",context)


def UserProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user,'rooms':rooms,'room_messages':room_messages,"topics":topics}
    return render(request,'base/profile.html',context)


@login_required(login_url='/login')
def create(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)




def update(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    if request.user != room.host:
        return HttpResponse("You cannot delete other people room!!") 
    
    if request.method == 'POST':
        form = RoomForm(request.POST,instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
        
    context = {'form':form}
    return render(request,"base/room_form.html",context)


@login_required(login_url='/login')
def delete(request,pk):
    room = Room.objects.get(id=pk)
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':room})


@login_required(login_url='/login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)
    
    if request.user != message.user:
        return HttpResponse('Your not allowed here!')
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})

