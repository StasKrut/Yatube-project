from django.shortcuts import render, get_object_or_404, redirect
from .models import Follow, Post, Group
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .utils import paginate_page
from django.views.decorators.cache import cache_page

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    # Одна строка вместо тысячи слов на SQL:
    posts = Post.objects.all()
    # В файле utils.py создал функцию paginate_page для паджинации
    page_obj = paginate_page(request, posts)
    # В словаре context отправляем
    # информацию в шаблон
    context = {
        'page_obj': page_obj,
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    # В файле utils.py создал функцию paginate_page для паджинации
    page_obj = paginate_page(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('author').filter(
        author__username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author__username=username
    ).exists()
    # В файле utils.py создал функцию paginate_page для паджинации
    page_obj = paginate_page(request, posts)
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=str(request.user))
        return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {'form': form,
               'is_edit': True,
               'post_id': post_id}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
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
    posts = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
        'posts': posts,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
