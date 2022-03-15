from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User

COUNT_POSTS = 10


@cache_page(20)
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.select_related("group")
    paginator = Paginator(post_list, COUNT_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.all(), COUNT_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, COUNT_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated and author != request.user:
        following = author.following.filter(user=request.user).exists()
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(Post.objects.select_related("author"), id=post_id)
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = "posts/create_post.html"
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", username=request.user)
    return render(request, template, {"form": form})


@login_required
def post_edit(request, post_id):
    template = "posts/create_post.html"
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    if request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect(post)
    form = PostForm(instance=post)
    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(post)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    authors_ids = Follow.objects.filter(
        user=request.user).values_list('author_id', flat=True)
    posts = Post.objects.filter(author_id__in=authors_ids)
    paginator = Paginator(posts, COUNT_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user_follow = get_object_or_404(Follow.objects,
                                    user=request.user,
                                    author=author)
    user_follow.delete()
    return redirect("posts:profile", author)
