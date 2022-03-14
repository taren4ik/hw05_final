from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая пост",
        )

        cls.public_urls_templates = (
            ("/", "posts/index.html"),
            (f"/group/{cls.group.slug}/", "posts/group_list.html"),
            (f"/profile/{cls.post.author}/", "posts/profile.html"),
        )

        cls.private_urls_templates = (
            (f"/posts/{cls.post.id}/edit/", "posts/create_post.html"),
            ("/create/", "posts/create_post.html"),
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username="author")
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_index_group_profile_url_exists_at_desired_location(self):
        """Страницы /index/, /group/test-slug/, /profile/auth/  доступны
        любому пользователю.
        """
        for url, _ in self.public_urls_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Страница /unexisting_page/  доступна любому пользователю."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_edit_post_url_redirect_anonymous(self):
        """Страницы /create/  и /posts/pk/edit/ перенаправляют
        неавторизованного пользователя.
        """

        for url, _ in self.private_urls_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                url_redirect = f"/auth/login/?next={url}"
                self.assertRedirects(response, url_redirect)

    def test_post_create_post_edit_exists_at_desired_location(self):
        """Страницы /post_create/, /post_edit/  доступны
        автору(авторизованному пользователю).
        """
        for url, _ in self.private_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in (
                self.private_urls_templates + self.public_urls_templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                