from django import forms
from .models import Comments, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('location', 'author', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class CommentsForm(forms.ModelForm):

    class Meta:
        model = Comments
        fields = ('text',)
