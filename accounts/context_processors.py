from accounts.models import Activity


def notification_context(request):
    if request.user.is_authenticated:
        # Surface recent activity count as lightweight notification badge data.
        count = Activity.objects.filter(user=request.user).count()
        return {
            'notification_count': count,
        }
    return {
        'notification_count': 0,
    }
