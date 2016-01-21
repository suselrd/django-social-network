# coding=utf-8
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.test import TestCase, Client


class GroupTest(TestCase):

    def setUp(self):
        # users
        self.users = {
            'user1': User.objects.create(username='pedro'),
            'user2': User.objects.create(username='juan'),
            'user3': User.objects.create(username='maria'),
            'user4': User.objects.create(username='jose'),
            'user5': User.objects.create(username='jesus'),
            'admin': User.objects.create(username='admin', is_staff=True, is_superuser=True),
        }

        # set passwords
        self.users['user1'].set_password('pedro')
        self.users['user1'].save(update_fields=["password"])
        self.users['user2'].set_password('juan')
        self.users['user2'].save(update_fields=["password"])
        self.users['user3'].set_password('maria')
        self.users['user3'].save(update_fields=["password"])
        self.users['user4'].set_password('jose')
        self.users['user4'].save(update_fields=["password"])
        self.users['user5'].set_password('jesus')
        self.users['user5'].save(update_fields=["password"])
        self.users['admin'].set_password('admin')
        self.users['admin'].save(update_fields=["password"])

        # test client
        self.client = Client()

    def test_group_creation(self):
        logged = self.client.login(username=self.users['user1'].username, password=self.users['user1'].username)
        self.assertTrue(logged)