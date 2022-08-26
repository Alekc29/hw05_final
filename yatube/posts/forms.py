from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа поста'),
            'image': ('Картинка поста'),
        }
        help_texts = {
            'text': ('Пиши текст поста, больше некому'),
            'group': ('Тут надо бы выбрать группу, но это необязательно'),
            'image': ('Если у вас есть картинка, вставляйте без стеснения')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
