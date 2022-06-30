from django.test import TestCase, Client
from ..models import Post, Group, Comment, Follow
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
import datetime
from django.core.cache import cache


User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response,
                                        template,
                                        'Некорректный шаблон')

    def test_pages_show_correct_text_in_context(self):
        """В шаблоны index, group_list, profile и post_detail
           сформированы с правильным текстом из словаря context."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})
            ): 'posts/post_detail.html',
        }
        for reverse_name in templates_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context.get('post').text,
                    'Тестовый пост',
                    'Текст не появился'
                )
                self.assertEqual(
                    response.context.get('post').group,
                    self.group,
                    'Группа не появилась'
                )
                self.assertEqual(
                    response.context.get('post').author,
                    self.user,
                    'Автор не появился'
                )
                self.assertEqual(
                    response.context.get('post').created.date(),
                    datetime.date.today(),
                    'Дата не появилась'
                )

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post.id})))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Проверяем, что типы полей формы в словаре
        # context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field,
                                      expected,
                                      'Не является экземпляром нужного класса')

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Проверяем, что типы полей формы в словаре
        # context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field,
                                      expected,
                                      'Не является экземпляром нужного класса')


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Страницы для тестирования
        self.test_page = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ): 'posts/profile.html',
        }
        cache.clear()

    def test_first_page_contains_ten_records(self):
        for reverse_name in self.test_page.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']),
                                 10,
                                 'Постов на первой странице не 10')

    def test_second_page_contains_three_records(self):
        for reverse_name in self.test_page.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                # Проверка: на второй странице должно быть три поста.
                self.assertEqual(len(response.context['page_obj']),
                                 3,
                                 'Постов на первой странице не 3')


class GroupViewsTest(TestCase):
    # Проверка, что новый пост на нужных страницах и в правильной группе.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.group2 = Group.objects.create(
            title='Тестовая группа',
            slug='test2_slug',
            description='Тестовое описание2',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Страницы для тестирования
        self.test_page = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ): 'posts/profile.html',
        }
        cache.clear()

    def test_new_post_in_right_pages(self):
        """Новый пост на нужных страницах."""
        for reverse_name in self.test_page.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                # Взяли первый элемент из списка и проверили,
                # что его содержание совпадает с ожидаемым
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                self.assertEqual(post_text_0,
                                 self.post.text,
                                 'Текст не появился')
                self.assertEqual(post_author_0,
                                 self.post.author,
                                 'Автор не появился')
                self.assertEqual(post_group_0,
                                 self.post.group,
                                 'Группа не появилась')

    def test_new_post_not_in_other_group(self):
        """Новый пост не попал в другую группу."""
        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                        kwargs={'slug': self.group2.slug})))
        self.assertEqual(len(response.context['page_obj']),
                         0,
                         'Пост в некорректной группе')


class Test_cache_index_page(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        initial_content = response.content.decode()
        self.post = Post.objects.create(
            text='Тестовый пост2',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверяем, что страница не поменялась, все посты из кеша
        self.assertEqual(
            initial_content,
            response.content.decode(),
            'Содержание страницы изменилось'
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверяем, что выдача поменялась
        self.assertNotEqual(
            initial_content,
            response.content.decode(),
            'Содержание страницы не изменилось'
        )


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='commentator')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

        cls.comment = Comment.objects.create(
            author=cls.user2,
            text='Тестовый коммент',
            post=cls.post
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        cache.clear()

    def test_guest_cannot_leave_comments(self):
        """Неавторизированный пользователь не может оставлять комментарии."""
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент1',
        }
        # Попробуем создать комментарий неавторизированным пользователем
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        # Проверим, что количество комментариев не увеличелось
        self.assertNotEqual(Comment.objects.count() + 1,
                            count_comments,
                            'Кол-во постов увеличилось')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='subscriber')
        cls.user3 = User.objects.create_user(username='non_subscriber')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user3)
        cache.clear()

    def test_follow_for_auth_user(self):
        """Авторизованный юзер может подписаться на другого юзера."""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Follow.objects.count(), 1, 'Подписка не добавилась')

    def test_content_for_follower_and_unfollow(self):
        """Подписанный юзер может отписываться."""
        self.follower = Follow.objects.create(
            user=self.user2, author=self.user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        self.follower.delete()
        response2 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(
            response.content.decode(),
            response2.content.decode(),
            'Подписка не удалилась'
        )

    def test_new_post_in_followers_feed(self):
        """Новая запись автора появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.user2,
            author=self.user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            response.context.get('post'),
            self.post,
            'Пост не появился в ленте подписчика'
        )
        response2 = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(
            response2.context.get('post'),
            self.post,
            'Пост появился в ленте неподписанного пользователя'
        )
