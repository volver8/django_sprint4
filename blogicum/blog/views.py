from datetime import datetime
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from .models import Category, Comments, Post
from .forms import CommentsForm, PostForm
from users.models import MyUser
from users.forms import CustomUserCreationForm


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
    model = Post
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        post = Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            pub_date__lte=datetime.now(),
            category__is_published=True
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        paginator = Paginator(post, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'page_obj': page_obj}
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'slug': self.object.author}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


def delete_post(request, post_id):
    instance = get_object_or_404(Post, pk=post_id, author=request.user)
    form = PostForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', context)


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        ).comments.all()
        context['comments'] = comments
        context['form'] = CommentsForm()
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category,
            slug=self.object.slug,
            is_published=True
        )
        post = Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            category__slug=self.object.slug,
            pub_date__lte=datetime.now(),
            category__is_published=True
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        paginator = Paginator(post, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'category': category,
            'page_obj': page_obj
        }
        return context


class ProfileDetailView(DetailView):
    model = MyUser
    slug_field = 'username'
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(MyUser, username=self.object.username)
        post = Post.objects.filter(
            author__username=self.object.username,
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        paginator = Paginator(post, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'profile': profile,
            'page_obj': page_obj
        }
        return context


class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = MyUser
    form_class = CustomUserCreationForm
    slug_field = 'username'
    template_name = 'blog/user.html'

    def test_func(self):
        object = self.get_object()
        return object == self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'slug': self.object.username}
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
