from django.urls import include, path

from . import views

app_name = 'blog'

post_urls = [
    path(
        'create/',
        views.PostCreateView.as_view(),
        name='create_post'
    ),
    path(
        '<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        '<int:post_id>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'
    ),
    path(
        '<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post_detail'
    ),
    path(
        '<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    path(
        '<int:post_id>/edit_comment/<int:comment_id>/',
        views.CommentsUpdateView.as_view(),
        name='edit_comment'
    ),
    path(
        '<int:post_id>/delete_comment/<int:comment_id>/',
        views.CommentsDeleteView.as_view(),
        name='delete_comment'
    ),

]

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/', include(post_urls)),
    path(
        'category/<slug:category_slug>/',
        views.CategoryListView.as_view(),
        name='category_posts'
    ),
    path(
        'profile/<username>/',
        views.ProfileListView.as_view(),
        name='profile'
    ),
    path(
        'edit',
        views.ProfileUpdateView.as_view(),
        name='edit_profile'
    )
]
