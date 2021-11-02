from django.shortcuts import redirect, render


def LandingView(request):
    pvetool_type = ["SB", "SOG", "SD"]

    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            if request.user.type_user in pvetool_type:
                return redirect("dashboard_syn")
            elif request.user.type_user == "B":
                return redirect("dashboard")

    # render the page
    context = {}
    return render(request, "LandingPage.html", context)

def validate(request):
    return render(request, "validate.txt")