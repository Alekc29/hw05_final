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
        cache.clear()

    def test_pages_uses_correct_template(self):
        ''' Проверка namespase:name и соответствующих шаблонов. '''
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
        ''' index, group, profile, detail с неверным контекстом. '''
        context = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'page_obj',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'post',
        }
        for revers, cont_obj in context.items():
            response = self.authorized_client.get(revers)
            if cont_obj == 'page_obj':
                first_object = response.context['page_obj'][0]
            else:
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
        cache.clear()

    def test_first_page_contains_ten_records(self):
        ''' Проверка: на первой странице должно быть 10 (PER_PAGE) постов. '''
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

    def setUp(self):
        cache.clear()

    def test_follower(self):
        ''' Тестируем подписку. '''
        follow_count = Follow.objects.count()
        self.authorized_user_fol_client.get(
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

    def test_unfollower(self):
        ''' Тестируем отписку. '''
        Follow.objects.create(
            user=self.user_unfol,
            author=self.author
        )
        follow_count = Follow.objects.count()
        self.authorized_user_unfol_client.get(
            reverse(
                'posts:profile_unfollow',
                args=[self.author.username]
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_post_appears_in_follow_page_for_followed_author(self):
        ''' Посты автора появляются на странице подписчика. '''
        group = self.group
        self.authorized_user_fol_client.get(
            reverse(
                'posts:profile_follow',
                args=[self.author.username]
            )
        )
        response_old = self.authorized_user_fol_client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj')),
            self.author.posts.count(),
            'Не загружается правильное колличество старых постов'
        )
        self.assertIn(
            self.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=self.author
        )
        response_new = self.authorized_user_fol_client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj')),
            self.author.posts.count(),
            'Нету нового поста'
        )
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост не верен'
        )

    def test_post_appers_in_follow_page_for_unfollowed_author(self):
        ''' Посты автора не появляются на странице неподписчика. '''
        response_old = self.authorized_user_unfol_client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj')),
            0,
            'Не загружается правильное колличество старых постов'
        )
        self.assertNotIn(
            self.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.author
        )
        response_new = self.authorized_user_unfol_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            len(response_new.context.get('page_obj')),
            0,
            'Новый пост не должен появляться'
        )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
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

    def test_cache_index_pages(self):
        ''' Проверяем работу кэша главной страницы. '''
        first_response = self.auth_client.get(reverse('posts:index'))
        anoter_post_note = 'Создаем еще один пост'
        Post.objects.create(
            text=anoter_post_note,
            author=self.author
        )
        response_after_post_add = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(
            first_response.content,
            response_after_post_add.content
        )
        cache.clear()
        response_after_cache_clean = self.auth_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            first_response.content,
            response_after_cache_clean.content
        )


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
