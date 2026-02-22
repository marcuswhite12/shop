from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm, ProfileUpdateForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile_view(request):
    return render(request, "users/profile.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")

    return render(request, "users/register.html", {"form": form})

@login_required
def profile_edit_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        instance=request.user
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("profile")

    return render(request, "users/profile_edit.html", {"form": form})