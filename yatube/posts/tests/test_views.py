import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text="тестовый текст",
            group=cls.group,
            image=cls.uploaded
        )

        cls.private_urls_templates = (
            (reverse('posts:post_edit',
                     args=str(cls.post.pk)), 'posts/create_post.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
        )
        cls.paginator_urls_templates = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile',
                     kwargs={'username': cls.user}), 'posts/profile.html'),
        )

        cls.public_urls_templates = cls.paginator_urls_templates + (
            (reverse('posts:post_detail', args=str(PostViewsTests.post.pk)),
             'posts/post_detail.html'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='author')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)

    def check_post_fields(self, post_object):
        post_text = post_object.text
        post_author = post_object.author
        post_group = post_object.group
        post_image = post_object.image
        self.assertEqual(post_text, PostViewsTests.post.text)
        self.assertEqual(post_author, PostViewsTests.post.author)
        self.assertEqual(post_group, PostViewsTests.post.group)
        self.assertEqual(post_image, PostViewsTests.post.image)

    def test_pages_uses_correct_template(self):
        """Имя шаблона использует соответствующий шаблон."""
        for reverse_name, template in (
                self.private_urls_templates + self.public_urls_templates):
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_page_show_correct_context(self):
        """Шаблоны index, group_list, profile, post_detail сформированы с
        правильным контекстом.
        """
        for reverse_name, _ in self.public_urls_templates:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if 'page_obj' in response.context:
                    post_object = response.context['page_obj'][0]
                else:
                    post_object = response.context.get('post')
                self.check_post_fields(post_object)

    def test_post_create_page_show_correct_context(self):
        """Шаблоны create_post, post_edit сформированы с правильным
        контекстом.
        """
        for reverse_name, _ in self.private_urls_templates:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.fields.ImageField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_index_group_list_profile_page_paginator(self):
        """Паджинатор в шаблонах index, group_list, profile работает корректно.
        """
        post_page_one = 10
        post_page_two = 3 + Post.objects.count()
        Post.objects.bulk_create(
            [
                Post(
                    author=PostViewsTests.user,
                    text='Тестовый пост',
                    group=PostViewsTests.group,
                )
                for _ in range(post_page_one + post_page_two - 1)
            ]
        )
        pages = (
            (1, post_page_one),
            (2, post_page_two),
        )

        for page, count in pages:
            for url, _ in self.paginator_urls_templates:
                with self.subTest(url=url):
                    response = self.authorized_client.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context['page_obj'].object_list), count
                    )

    def test_post_not_included_in_group(self):
        """Пост не принадлежит другой группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )

        group_2 = PostViewsTests.group = Group.objects.create(
            title='Заголовок2'
        )
        post_object = response.context['page_obj'][0]
        post_group = post_object.group.pk
        self.assertNotEqual(post_group, group_2.pk)

    def test_cache_index(self):
        """Работает кэш на главной странице."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.post.delete()
        response_update = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_update.content)
        cache.clear()
        response_clear_page = self.guest_client.get(reverse('posts:index'))
        self.assertTrue(response.content != response_clear_page)

    def test_profile_follow(self):
        """Работает подписка автора."""
        user_second = User.objects.create_user(username='new_user')
        follow_before = Follow.objects.count()

        self.authorized_client.get(
            reverse(
                'posts:profile_follow', kwargs={'username': user_second}))
        follow_after = Follow.objects.count()
        self.assertEqual(follow_before + 1, follow_after)

    def test_profile_unfollow(self):
        """Работает отписка автора."""
        user_second = User.objects.create_user(username='new_user')
        Follow.objects.create(author=user_second, user=PostViewsTests.user)
        follow_before = Follow.objects.filter(author=user_second).count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': user_second}))
        follow_after = Follow.objects.count()
        self.assertEqual(follow_before - 1, follow_after)
        print(Follow.objects.count())

    def test_user_cannot_follow_himself(self):
        """Пользователь не может подписаться на себя."""
        follow_before = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewsTests.user})
        )
        self.assertEqual(follow_before, Follow.objects.count())

    def test_add_new_post_follower_and_cannot_post_not_follower(self):
        """Новая запись появляется у подписчиков и не появляется у тех,
        кто не подписан."""
        user_second = User.objects.create_user(username='second_user')
        self.authorized_client_second = Client()
        self.authorized_client_second.force_login(user_second)
        user_third = User.objects.create_user(username='third_user')
        self.authorized_client_third = Client()
        self.authorized_client_third.force_login(user_third)
        self.authorized_client_second.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostViewsTests.user}))

        response_auth_client_second_before = self.authorized_client_second.get(
            reverse('posts:follow_index')
        )
        count_post_follower_before = len(
            response_auth_client_second_before.context['page_obj'])

        response_auth_client_third_before = self.authorized_client_third.get(
            reverse('posts:follow_index')
        )
        count_post_not_follower_before = len(
            response_auth_client_third_before.context.get('page_obj'))

        Post.objects.create(
            author=PostViewsTests.user,
            text="тестовый текст",
        )
        response_auth_client_second_after = self.authorized_client_second.get(
            reverse('posts:follow_index')
        )
        count_post_follower_after = len(
            response_auth_client_second_after.context['page_obj'])

        response_auth_client_third_after = self.authorized_client_third.get(
            reverse('posts:follow_index')
        )
        count_post_not_follower_after = len(
            response_auth_client_third_after.context['page_obj'])

        self.assertEqual(
            count_post_follower_before + 1, count_post_follower_after)
        self.assertEqual(
            count_post_not_follower_before, count_post_not_follower_after)
