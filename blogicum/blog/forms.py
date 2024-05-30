from django import forms
from .models import Comments, Post


# Для использования формы с моделями меняем класс на forms.ModelForm.
class PostForm(forms.ModelForm):
    # Удаляем все описания полей.

    # Все настройки задаём в подклассе Meta.
    class Meta:
        # Указываем модель, на основе которой должна строиться форма.
        model = Post
        # Указываем, что надо отобразить все поля.
        fields = ( 'image', 'title', 'text', 'category', 'pub_date', )
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'date'})
        }


class CommentsForm(forms.ModelForm):

    class Meta:
        model = Comments
        fields = ('text',)
