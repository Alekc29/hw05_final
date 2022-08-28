from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User
from posts.views import PER_PAGE


class PostPagesTests(TestCase):
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
            group=cls.group,
            text='Тестовый пост'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        ''' Проверка namespase:name и соответствующих шаблонов. '''
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_profile_show_correct_context(self):
        ''' index, group, profile с неверным контекстом. '''
        cache.clear()
        context = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_list', kwargs={'slug': self.group.slug})),
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username})),
        ]
        for response in context:
            first_object = response.context['page_obj'][0]
            context_objects = {
                self.post.author: first_object.author,
                self.post.text: first_object.text,
                self.group.slug: first_object.group.slug,
                self.post.id: first_object.id,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(response_name, reverse_name)

    def test_detail_page_correct_context(self):
        ''' Шаблон post_detail сформирован с неправильным контекстом. '''
        reverse_name = reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.post.id}'}
        )
        response = self.authorized_client.get(reverse_name)
        first_object = response.context['post']
        context_objects = {
            self.post.author: first_object.author,
            self.post.text: first_object.text,
            self.group.slug: first_object.group.slug,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)


class PaginatorViewsTest(TestCase):
    ''' Тестируем пагинатор на страницах index, group_list, profile. '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.SECOND_PAGE = 3
        objs = [
            Post(
                author=cls.user,
                group=cls.group,
                text=f'test-post {i}'
            )
            for i in range(cls.SECOND_PAGE + PER_PAGE)
        ]
        cls.post = Post.objects.bulk_create(objs=objs)

    def setUp(self):
        self.client = Client()
        self.url_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
        }

    def test_first_page_contains_ten_records(self):
        ''' Проверка: на первой странице должно быть 10 (PER_PAGE) постов. '''
        cache.clear()
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        ''' Проверка: на второй странице должно быть 3 поста. '''
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.SECOND_PAGE
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.user_fol = User.objects.create_user(
            username='test_user_follow'
        )
        cls.authorized_user_fol_client = Client()
        cls.authorized_user_fol_client.force_login(cls.user_fol)
        cls.user_unfol = User.objects.create_user(
            username='test_user_unfollow'
        )
        cls.authorized_user_unfol_client = Client()
        cls.authorized_user_unfol_client.force_login(cls.user_unfol)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_new_author_post_for_follower(self):
        ''' Тестируем подписку. '''
        cache.clear()
        client = self.authorized_user_fol_client
        follow_count = Follow.objects.count()
        client.get(
            reverse(
                'posts:profile_follow',
                args=[self.author.username]
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        follow_obj = Follow.objects.get(
            author=self.author.id,
            user=self.user_fol.id,
        )
        fol_obj = {
            self.author: follow_obj.author,
            self.user_fol: follow_obj.user,
        }
        for form, obj in fol_obj.items():
            with self.subTest(form=form):
                self.assertEqual(obj, form)

    def test_new_author_post_for_unfollower(self):
        ''' Тестируем отписку. '''
        cache.clear()
        client = self.authorized_user_unfol_client
        Follow.objects.create(
            user=self.user_unfol,
            author=self.author
        )
        follow_count = Follow.objects.count()
        client.get(
            reverse(
                'posts:profile_unfollow',
                args=[self.author.username]
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_index(self):
        ''' Тестируем follow_index. '''
        cache.clear()
        client = self.authorized_user_unfol_client
        response_old = client.get(reverse('posts:follow_index'))
        old_posts = response_old.context.get('page_obj').object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            0,
            'Не загружается правильное колличество старых постов'
        )
        self.assertNotIn(
            self.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.author
        )
        response_new = client.get(reverse('posts:follow_index'))
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            0,
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Проверка кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_old = self.authorized_client.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = self.authorized_client.get(
            reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='test_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth_user)
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_add_comment(self):
        ''' Тест добавления коммента к посту. '''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'test-comment',
        }
        response = self.auth_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        comment_obj = Comment.objects.first()
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
        ).exists())
        self.assertEqual(comment_obj.author, self.auth_user)
