from django.contrib import admin
from .models import Post, Group, Comment, Follow


# Регистрируем класс PostAdmin для модели Post через декоратор
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'created', 'author', 'group',)
    list_editable = ('group',)
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('created',)
    empty_value_display = '-пусто-'


admin.site.register(Group)

admin.site.register(Comment)

admin.site.register(Follow)
