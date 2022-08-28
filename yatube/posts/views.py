from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator

PER_PAGE = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    ''' Главная страница. '''
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    posts = Post.objects.select_related('author', 'group')
    page_obj = paginator(request, posts, PER_PAGE)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    ''' Страница группы. '''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    title = Group.__str__
    posts = group.posts.select_related('author')
    page_obj = paginator(request, posts, PER_PAGE)
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    ''' Страница всех постов автора. '''
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    count = author.posts.count()
    page_obj = paginator(request, posts, PER_PAGE)
    following = request.user.is_authenticated and \
        Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    context = {
        'author': author,
        'count': count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    ''' Страница детальной информации поста. '''
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(add_comment(request, post_id))
    comments = Comment.objects.filter(post=post_id)
    count = Post.objects.select_related('author').count()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'count': count,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    ''' Страница создания нового поста. '''
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    ''' Страница изменения поста. '''
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    ''' Форма добавления комментариев к постам. '''
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    ''' Главная страница избранных авторов. '''
    template = 'posts/follow.html'
    title = 'Посты авторов, на которые подписаны'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, posts, PER_PAGE)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    ''' Функция подписки на автора. '''
    follower = Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).exists()
    if request.user.username != username and not follower:
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username),
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    ''' Функция отписки от автора. '''
    follower = Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    if follower:
        follower.delete()
    return redirect('posts:profile', username=username)
