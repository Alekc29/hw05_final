from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def test_about_url_exists_at_desired_location(self):
        ''' Проверка доступности адреса /author/ и /tech/. '''
        for address in self.templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        ''' Проверка шаблона для адреса /author/ и /tech/. '''
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)


class AboutViewTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.templates_url_names = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }

    def test_about_page_accessible_by_name(self):
        ''' URL, генерируемый при помощи имени about:-//-, доступен. '''
        for address in self.templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(reverse(address))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        ''' При запросе к about:-//- применяется соответствующий шаблон. '''
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(reverse(address))
                self.assertTemplateUsed(response, template)
