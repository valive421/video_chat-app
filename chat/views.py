from django.shortcuts import render,redirect

# Create your views here.
def redirect_to_chat(request):
    if request.user.is_authenticated:
        return redirect('main-view', username=request.user.username)  # Redirect to /chat/<username>/
    return redirect('login')  # Redirect unauthenticated users to login

def main_view(request,username):
    context ={}
    return render(request,'chat/main.html', {'username': username})


