from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    ROLE_CHOICES = (
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
        ('ADMIN', 'Admin'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='FREE')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_active_workspace(self):
        # Returns the first workspace where the user is a member
        workspace = Workspace.objects.filter(members__user=self).first()
        if not workspace:
            workspace = Workspace.objects.create(name=f"{self.username}'s Workspace", owner=self)
            from accounts.models import WorkspaceMember
            WorkspaceMember.objects.get_or_create(workspace=workspace, user=self, role='ADMIN')
        return workspace

class Company(models.Model):
    GOAL_CHOICES = (
        ('Recruitment', 'Recruitment Analytics'),
        ('Company Growth', 'Company Growth Analytics'),
        ('Sales', 'Sales Analytics'),
        ('General', 'General Data Analysis'),
    )

    name = models.CharField(max_length=150)
    industry = models.CharField(max_length=100, blank=True, null=True)
    primary_goal = models.CharField(max_length=50, choices=GOAL_CHOICES, default='General')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', default='profiles/default-profile.svg')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email 

class Activity(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    title=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Workspace(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_workspaces')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('EDITOR', 'Editor'),
        ('VIEWER', 'Viewer'),
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.workspace.name} ({self.role})"


class Theme(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='theme')
    background_color = models.CharField(max_length=50, default='#0f172a')  # Default dark slate
    primary_color = models.CharField(max_length=50, default='#3b82f6')     # Default blue
    layout_mode = models.CharField(max_length=20, default='modern')        # modern, classic, minimal
    is_dark_mode = models.BooleanField(default=True)
    background_image = models.ImageField(upload_to='themes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Theme"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_theme(sender, instance, created, **kwargs):
    if created:
        Theme.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_theme(sender, instance, **kwargs):
    try:
        instance.theme.save()
    except Theme.DoesNotExist:
        pass


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_workspace(sender, instance, created, **kwargs):
    if created:
        workspace = Workspace.objects.create(
            name=f"{instance.username}'s Workspace",
            owner=instance
        )
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=instance,
            role='ADMIN'
        )