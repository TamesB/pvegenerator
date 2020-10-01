from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

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

def token(request):
    identity = request.user.username
    device_id = request.GET.get('device', 'default')  # unique device ID

    account_sid = settings.TWILIO_ACCOUNT_SID
    api_key = settings.TWILIO_API_KEY
    api_secret = settings.TWILIO_API_SECRET
    chat_service_sid = settings.TWILIO_CHAT_SERVICE_SID

    token1 = AccessToken(account_sid, api_key, api_secret, identity=identity)

    # Create a unique endpoint ID for the device
    endpoint = "MyDjangoChatRoom:{0}:{1}".format(identity, device_id)

    if chat_service_sid:
        chat_grant = ChatGrant(endpoint_id=endpoint,
                               service_sid=chat_service_sid)
        token1.add_grant(chat_grant)

    response = {
        'identity': identity,
        'token': token1.to_jwt().decode('utf-8')
    }

    return JsonResponse(response)
