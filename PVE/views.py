from django.shortcuts import render, redirect


def LandingView(request):
    syntrus_type = ["SB", "SOG", "SD"]

    # cant see lander page if already logged in
    if request.user:
        if request.user.is_authenticated:
            if request.user.type_user in syntrus_type:
                return redirect('dashboard_syn')
            elif request.user.type_user == 'B':
                return redirect('dashboard')

    # render the page
    context = {}
    return render(request, 'LandingPage.html', context)
