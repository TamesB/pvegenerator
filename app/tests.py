from django.test import TestCase, Client
from django.contrib import auth
from .models import CustomUser
import os
from django.conf import settings

OK = 200
SERVER_ERROR = 500
TIMEOUT = 504
BAD_GATEWAY = 502
NOT_IMPLEMENTED = 501
OVERLOAD = 503
NOT_FOUND = 404
class LoginTest(TestCase):
    def setUp(self):
        CustomUser.objects.create(username="admintest", password="testpass", type_user="B")
        CustomUser.objects.create(username="thirdpartytest", password="testpass", type_user="SD")
        CustomUser.objects.create(username="projmanagertest", password="testpass", type_user="SOG")
        CustomUser.objects.create(username="thirdadmintest", password="testpass", type_user="SB")
        
    def test_admin_AdminLogin(self):
        response = self.client.post('/login/', {'username': 'admintest', 'password': 'testpass'})
        user = auth.get_user(self.client)
        self.assert_equal(user.is_authenticated, True)

    def test_Third_AdminLogin(self):
        response = self.client.post('/login/', {'username': 'thirdpartytest', 'password': 'testpass'})
        user = auth.get_user(self.client)
        self.assert_equal(user.is_authenticated, False)

    def test_ProjManager_AdminLogin(self):
        response = self.client.post('/login/', {'username': 'projmanagertest', 'password': 'testpass'})
        user = auth.get_user(self.client)
        self.assert_equal(user.is_authenticated, False)

    def test_ThirdAdmin_AdminLogin(self):
        response = self.client.post('/login/', {'username': 'thirdadmintest', 'password': 'testpass'})
        user = auth.get_user(self.client)
        self.assert_equal(user.is_authenticated, False)
        
        
class EntryTest(TestCase):
    def setUp(self):
        CustomUser.objects.create(username="thirdpartytest", password="testpass", type_user="SD")
        CustomUser.objects.create(username="projmanagertest", password="testpass", type_user="SOG")
        CustomUser.objects.create(username="thirdadmintest", password="testpass", type_user="SB")
