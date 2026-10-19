from .permissions import is_approver

def permissions(request):
    """ส่งตัวแปร is_approver ให้ทุก template (หัวหน้า/แอดมิน = True, พนักงานทั่วไป = False)"""
    user = getattr(request, 'user', None)
    return {'is_approver': bool(user and user.is_authenticated and is_approver(user))}