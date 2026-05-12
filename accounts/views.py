from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, ProfileForm, ActivityForm
from .models import Profile, Activity, Company, Workspace, WorkspaceMember
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Theme
import json
from django.http import JsonResponse
from django.contrib import messages

def register_view(request):
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            subject = 'Welcome to Data Analysis!'
            message = f'Hi {user.username},\n\nThank you for registering for Data Analysis. We are excited to have you on board!\n\nBest regards,\nThe Data Analysis Team'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            except Exception as e:
                # Log the error or handle it silently so registration still succeeds
                print(f"Failed to send welcome email: {e}")
                
            login(request, user)
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.company is None:
                return redirect('onboarding')
            return redirect('dashboard')

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.company is None:
                return redirect('onboarding')
            return redirect('dashboard')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    activities = Activity.objects.filter(user=request.user).order_by('-date')
    company = profile.company

    profile_form = ProfileForm(instance=profile)
    activity_form = ActivityForm()

    if request.method == "POST":

        if "profile_submit" in request.POST:
            profile_form = ProfileForm(
                request.POST,
                request.FILES,
                instance=profile
            )
            if profile_form.is_valid():
                profile_form.save()
                return redirect('profile')

        if "activity_submit" in request.POST:
            activity_form = ActivityForm(request.POST)
            if activity_form.is_valid():
                activity = activity_form.save(commit=False)
                activity.user = request.user
                activity.save()
                return redirect('profile')

        if "company_submit" in request.POST:
            company_name = request.POST.get('company_name', '').strip()
            industry = request.POST.get('industry', '').strip()
            primary_goal = request.POST.get('primary_goal', 'General')

            allowed_goals = {choice[0] for choice in Company.GOAL_CHOICES}
            if primary_goal not in allowed_goals:
                primary_goal = 'General'

            if not company_name:
                messages.error(request, 'Company name is required to update category mode.')
                return redirect('profile')

            if company:
                company.name = company_name
                company.industry = industry
                company.primary_goal = primary_goal
                company.save()
            else:
                company = Company.objects.create(
                    name=company_name,
                    industry=industry,
                    primary_goal=primary_goal,
                )
                profile.company = company
                profile.save()

            workspace = request.user.get_active_workspace()
            workspace.name = f"{company_name}'s Workspace"
            workspace.save()

            messages.success(request, f"Workspace category updated to {primary_goal}.")
            return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'activity_form': activity_form,
        'activities': activities,
        'goal_choices': Company.GOAL_CHOICES,
        'company': company,
    })


@login_required
def notifications_view(request):
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:30]
    return render(request, 'accounts/notifications.html', {
        'activities': activities,
    })

@login_required
def update_theme(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            theme, _ = Theme.objects.get_or_create(user=request.user)
            
            if 'background_color' in data:
                theme.background_color = data['background_color']
            if 'primary_color' in data:
                theme.primary_color = data['primary_color']
            if 'is_dark_mode' in data:
                theme.is_dark_mode = data['is_dark_mode']
            if 'layout_mode' in data:
                theme.layout_mode = data['layout_mode']
                
            theme.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def onboarding_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Already onboarded — skip to dashboard
    if profile.company is not None:
        return redirect('dashboard')

    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        industry = request.POST.get('industry', '').strip()
        primary_goal = request.POST.get('primary_goal', 'General')
        allowed_goals = {choice[0] for choice in Company.GOAL_CHOICES}
        if primary_goal not in allowed_goals:
            primary_goal = 'General'

        if company_name:
            company = Company.objects.create(
                name=company_name,
                industry=industry,
                primary_goal=primary_goal,
            )
            profile.company = company
            profile.save()

            # Rename the user's default workspace to match the company name
            workspace = request.user.get_active_workspace()
            workspace.name = f"{company_name}'s Workspace"
            workspace.save()

            return redirect('dashboard')

    return render(request, 'accounts/onboarding.html', {
        'goal_choices': Company.GOAL_CHOICES,
    })