from datetime import datetime

from django.http import Http404
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from .models import Category, Comments, Post
from .forms import CommentsForm, PostForm
from users.models import MyUser
from users.forms import CustomUserCreationForm


POSTS_NUM = 10


User = get_user_model()


def get_posts(add_filter=False, add_comments=False):
    queryset = Post.objects.select_related(
        'category', 'location', 'author'
    )
    if add_filter:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now()
        )
    if add_comments:
        queryset = queryset.annotate(comment_count=Count('comments'))
    queryset = queryset.order_by(
        '-pub_date'
    )
    return queryset


def get_category_object(category):
    return get_object_or_404(Category, slug=category)


def get_category_posts(category):
    object = get_category_object(category)
    if object.is_published is False:
        raise Http404
    queryset = get_posts(True, True).filter(category__slug=category)
    return queryset


def get_user(username):
    return get_object_or_404(User, username=username)


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        object = self.get_object()
        return redirect(
            'blog:post_detail',
            object.pk
        )


class PostListView(ListView):
    queryset = get_posts(True, True)
    paginate_by = POSTS_NUM
    template_name = 'blog/index.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.object.author.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    context_object_name = 'form'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.get_object())
        context['form'] = form
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:index'
        )


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    pk_field = 'post_id'
    template_name = 'blog/detail.html'

    def get_object(self):
        object = super().get_object()
        date_now = datetime.now().date()
        check_author = object.author != self.request.user
        check_is_pub = object.is_published is False
        check_cat_is_pub = object.category.is_published is False
        check_date = date_now < object.pub_date.date()
        if ((check_author) & (check_is_pub or check_cat_is_pub or check_date)):
            raise Http404
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.get_object().comments.all()
        context['form'] = CommentsForm()
        return context


class CategoryListView(ListView):
    slug_url_kwarg = 'category_slug'
    paginate_by = POSTS_NUM
    template_name = 'blog/category.html'

    def get_queryset(self):
        queryset = get_category_posts(self.kwargs['category_slug'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_category_object(self.kwargs['category_slug'])
        context['category'] = category
        return context


class ProfileListView(ListView):
    slug_url_kwarg = 'username'
    paginate_by = POSTS_NUM
    template_name = 'blog/profile.html'

    def get_queryset(self):
        get_user(self.kwargs['username'])
        if self.kwargs['username'] != self.request.user.username:
            return get_posts(True, True).filter(
                author__username=self.kwargs['username']
            )
        else:
            return get_posts(False, True).filter(
                author__username=self.kwargs['username']
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_user(self.kwargs['username'])
        context['profile'] = profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = MyUser
    form_class = CustomUserCreationForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.object.username}
        )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentsForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


class CommentsUpdateView(OnlyAuthorMixin, UpdateView):
    model = Comments
    pk_url_kwarg = 'comment_id'
    form_class = CommentsForm
    context_object_name = 'comment'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post_id}
        )


class CommentsDeleteView(OnlyAuthorMixin, DeleteView):
    model = Comments
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post_id}
        )
