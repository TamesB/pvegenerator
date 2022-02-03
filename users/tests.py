# Create your tests here.
from django.test import TestCase, Client
from .models import CustomUser

class SignUpTest(TestCase):
    def signup_test(self):
        user = CustomUser.objects.create(username="testcase", password="testpass")
