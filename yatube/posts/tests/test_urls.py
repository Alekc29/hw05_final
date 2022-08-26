from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        self.urls_name_public_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        self.urls_name_private_templates = {
            '/create/': 'posts/create_post.html',
        }
        self.urls_name_author_templates = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }

    def test_guest_url(self):
        ''' Тестируем доступные адреса гостю. '''
        for address in self.urls_name_public_templates:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirect_url(self):
        ''' Тестируем редирект адреса гостя. '''
        for address in self.urls_name_private_templates:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, '/auth/login/?next=/create/')
        for address in self.urls_name_author_templates:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    '/auth/login/?next=/posts/1/edit/'
                )

    def test_user_url(self):
        ''' Тестируем доступные адреса пользователю. '''
        for address in {**self.urls_name_public_templates,
                        **self.urls_name_private_templates}:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_redirect_url(self):
        ''' Тестируем редирект адреса пользователя. '''
        for address in self.urls_name_author_templates:
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_author_url(self):
        ''' Тестируем доступные адреса автору. '''
        for address in {**self.urls_name_public_templates,
                        **self.urls_name_private_templates,
                        **self.urls_name_author_templates}:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting(self):
        """Несуществующая страница выдаёт код 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        ''' URL-адрес использует соответствующий шаблон. '''
        cache.clear()
        for address, template in {**self.urls_name_public_templates,
                                  **self.urls_name_private_templates,
                                  **self.urls_name_author_templates}.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
