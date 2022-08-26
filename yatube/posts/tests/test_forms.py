import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group_edit = Group.objects.create(
            title='Тестовая группа edit',
            slug='test-edit-slug',
            description='Тестовое описание edit'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        ''' Создаёт авторизованный клиент. '''
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        ''' Валидная форма создает запись в Post. '''
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем статус response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным постом
        self.assertTrue(
            Post.objects.filter(
                author=form_data['author'],
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        create_object = response.context['post']
        context_objects = {
            form_data['author']: create_object.author,
            form_data['text']: create_object.text,
            form_data['group']: create_object.group.id,
            'posts/small.gif': create_object.image,
        }
        for form, response_name in context_objects.items():
            with self.subTest(form=form):
                self.assertEqual(response_name, form)

    def test_edit_post(self):
        ''' Валидная форма изменяет запись в Post. '''
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        form_data = {
            'author': self.user,
            'text': 'Изменённый тестовый пост',
            'group': self.group_edit.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{post.id}'}
            ),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{post.id}'}
        ))
        # Проверяем, что запись изменена с заданным постом
        self.assertTrue(
            Post.objects.filter(
                author=form_data['author'],
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        edit_object = response.context['post']
        context_objects = {
            form_data['author']: edit_object.author,
            form_data['text']: edit_object.text,
            form_data['group']: edit_object.group.id,
        }
        for form, response_name in context_objects.items():
            with self.subTest(form=form):
                self.assertEqual(response_name, form)
