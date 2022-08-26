from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Заголовок',
        max_length=200,
        help_text='заголовок группы'
    )
    slug = models.SlugField(
        default='group1',
        unique=True
    )
    description = models.TextField(
        'Описание',
        help_text='Описание группы'
    )

    def __str__(self):
        return f'Записи сообщества {self.title}'


class Post(models.Model):
    text = models.TextField(
        'Текст',
        help_text='Текст написал автор',
        validators=[MinLengthValidator(1)],
    )
    pub_date = models.DateTimeField(
        'Дата',
        auto_now_add=True,
        help_text='Дата создания поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа автора',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return f'{self.text[:15]}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(

    )
    created = models.DateTimeField(
        'Дата',
        auto_now_add=True,
        help_text='Дата создания поста',
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('author',)
