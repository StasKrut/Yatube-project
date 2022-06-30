from django.test import TestCase, Client, override_settings

from ..models import Post, Group, Comment
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

import shutil
import tempfile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


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
        cls.group2 = Group.objects.create(
            title='Новая группа',
            slug='test2_slug',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=User.objects.get(username='auth'),
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_forms_create_post(self):
        """Проверим, что при создании нового поста
           увеличевается кол-во постов и
           пользователь перенаправяется в профайл"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост1',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(),
                         count_posts + 1,
                         'Кол-во постов не увеличилось')
        # Проверяем правильно ли записался пост в БД
        # пост должен быть первым в списке
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text,
                         'Тестовый пост1',
                         'Пост не записался')
        
    def test_forms_edit_post(self):
        """Проверим, что после редактирования поста
           происходит его измеение в БД"""
        form_data = {
            'text': 'Редактированный пост',
            'group': self.group2.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(post_edit.text,
                         'Редактированный пост',
                         'Пост не изменился в БД')
        self.assertEqual(post_edit.group,
                         self.group2,
                         'Группа не изменилась в БД')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImgViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_image_in_new_post(self):
        """Новый пост выдается с картинкой."""
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
                    response.context.get('post').image,
                    'posts/small.gif',
                    'Картинка не появилась'
                )

    def test_image_in_database(self):
        """Проверим, что при создании нового поста
           картинка записывается в БД"""
        form_data = {
            'text': 'Тестовый пост1',
            'group': self.group.id,
            'image': 'posts/small.gif',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        # Проверяем правильно ли записался пост в БД
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост1',
                image__isnull=False,
            ).exists()
        )


class CommentFormsTest(TestCase):
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
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_comments_shown_on_post_detail_page(self):
        """Комментарии после успешной отправки
        отображаются на странице поста."""
        form_data = {
            'text': 'Тестовый коммент1',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context.get('comments')[1].text,
            'Тестовый коммент1',
            'Комментарий не отображается'
        )
