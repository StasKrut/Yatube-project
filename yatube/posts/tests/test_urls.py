from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.cache import cache

User = get_user_model()


class PostUrlsTest(TestCase):
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
        )
        cls.user2 = User.objects.create_user(username='auth2')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Создаем второй авторизованный клиент
        self.authorized_client2 = Client()
        # Авторизуем второго пользователя
        self.authorized_client2.force_login(self.user2)
        cache.clear()

    def test_public_urls_is_available(self):
        """Страницы доступны любому пользователю."""
        # Шаблоны по адресам
        public_url = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for path in public_url.keys():
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 f'Статус код страницы не {path} не равен 200')

    def test_authorized_urls_is_available(self):
        """Страницы доступны авторизированному пользователю."""
        # Шаблоны по адресам
        authorized_url = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for path in authorized_url.keys():
            with self.subTest(path=path):
                response = self.authorized_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 f'Статус код страницы не {path} не равен 200')

    def test_authorized_url_redirect_anonymous_login(self):
        """Страницы для авторизированного пользователя
        перенаправляют анонимного пользователя
        на страницу логина."""
        authorized_url = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for path in authorized_url.keys():
            with self.subTest(path=path):
                response = self.guest_client.get(path, follow=True)
                self.assertRedirects(
                    response, '/auth/login/' + '?next=' + path
                )

    def test_post_edit_url_redirect_not_author(self):
        """Страница редактирования чужого поста
        перенаправляет пользователя на страницу поста."""
        response = self.authorized_client2.get(
            (f'/posts/{self.post.id}/edit/'),
            follow=True
        )
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/')
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        all_url = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for path, template in all_url.items():
            with self.subTest(path=path):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(
                    response,
                    template,
                    'URL-адрес использует некорректный шаблон'
                )

    def test_non_existent_url_return_error_404(self):
        """Запрос к несуществующей странице возращает ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code,
                         HTTPStatus.NOT_FOUND,
                         'Ошибка 404 не возвращается')
        # Проверка использования кастомизированного шаблона при ошибке
        self.assertTemplateUsed(
            response,
            'core/404.html',
            'Некорректный шаблон ошибки'
        )
