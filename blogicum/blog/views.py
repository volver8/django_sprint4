from datetime import datetime
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponseNotFound
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from .models import Category, Comments, Post
from .forms import CommentsForm, PostForm
from users.models import MyUser
from users.forms import CustomUserCreationForm


User = get_user_model()


def get_posts_base_queryset(
        is_published=False,
        category_is_published=False,
        category_slug=False,
        author=False,
        pub_date=False):
    queryset = Post.objects.select_related(
        'category', 'location', 'author'
    )
    if is_published:
        queryset = queryset.filter(is_published=True)
    if pub_date:
        queryset = queryset.filter(pub_date__lte=datetime.now())
    if category_is_published:
        queryset = queryset.filter(category__is_published=True)
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if author:
        queryset = queryset.filter(author__username=author)
    queryset = queryset.order_by(
        '-pub_date'
    ).annotate(comment_count=Count('comments'))
    return queryset


def get_category_object(slug):
    object = get_object_or_404(Category, slug=slug)
    return object


def get_comments_base_queryset(post_id):
    queryset = Comments.objects.select_related(
        'author',
        'post'
    ).filter(post=post_id)
    return queryset


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
    queryset = get_posts_base_queryset(True, True, False, False, True)
    paginate_by = 10
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
        instance = self.get_object()
        form = PostForm(instance=instance)
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
        if object.author != self.request.user:
            if object.is_published is False:
                raise Http404
            if object.category.is_published is False:
                raise Http404
            if date_now < object.pub_date.date():
                raise Http404
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = get_comments_base_queryset(self.object.pk)
        context['form'] = CommentsForm()
        return context


class CategoryListView(ListView):
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_queryset(self):
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        if category.is_published is False:
            raise Http404
        queryset = get_posts_base_queryset(
            True,
            True,
            self.kwargs['category_slug'],
            False,
            True
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        paginator = Paginator(self.get_queryset(), 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'category': category,
            'page_obj': page_obj
        }
        return context


class ProfileListView(ListView):
    slug_url_kwarg = 'username'
    template_name = 'blog/profile.html'

    def get_queryset(self):
        if self.kwargs['username'] != self.request.user.username:
            queryset = get_posts_base_queryset(
                True,
                True,
                False,
                self.kwargs['username'],
                True
            )
            return queryset
        return get_posts_base_queryset(False, False, False, self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(MyUser, username=self.kwargs['username'])
        paginator = Paginator(self.get_queryset(), 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'profile': profile,
            'page_obj': page_obj
        }
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = MyUser
    form_class = CustomUserCreationForm
    template_name = 'blog/user.html'

    def get_object(self):
        object = self.request.user
        return object

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
