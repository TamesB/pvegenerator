from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

class LoginRequiredMixin(object):
    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
    

class LogoutIfNotStaffMixin(AccessMixin):
        def dispatch(self, request, *args, **kwargs):
            if not request.user.is_staff:
                logout(request)
                return redirect("login")
            return super(LogoutIfNotStaffMixin, self).dispatch(request, *args, **kwargs)
