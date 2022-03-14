import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Заголовок",
            slug="test-slug",
            description="Тестовое описание",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.guest_client = Client()

    def test_edit(self):
        """Валидная форма создает, редактирует запись в Post."""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text="Тестовый пост",
        )

        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст", "group": PostCreateFormTests.group.pk
        }

        response = self.authorized_client.post(
            reverse(
                "posts:post_edit", args=str(
                    post.pk)), data=form_data, follow=True
        )

        self.assertRedirects(
            response, reverse("posts:post_detail", args=str(post.pk))
        )

        response_guest_client = self.guest_client.post(
            reverse(
                "posts:post_edit", args=str(
                    post.pk)), data=form_data, follow=True
        )

        self.assertRedirects(
            response_guest_client, "/auth/login/?next=/posts/1/edit/"
        )
        self.assertEqual(Post.objects.count(), posts_count)

        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                author=post.author,
                group=PostCreateFormTests.group.pk,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            "text": "Тестовый текст",
            "group": PostCreateFormTests.group.pk,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response, reverse("posts:profile", kwargs={"username": "auth"})
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                author=self.user,
                group=PostCreateFormTests.group.pk,
                image="posts/small.gif"
            ).exists()
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_not_create_guest_client(self):
        """Валидная форма не создает запись в Post под гостем."""
        form_data = {
            "text": "Тестовый текст",
        }

        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(response, "/auth/login/?next=/create/")

        self.assertEqual(Post.objects.count(), posts_count)

    def test_comments_create_auth_client(self):
        """Валидная форма не создает комментарий в Post под гостем."""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text="Тестовый пост",
        )

        form_data = {
            "text": "тестовый коммент",
        }

        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse(
                "posts:add_comment", args=str(post.pk)), data=form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse("posts:post_detail", args=str(post.pk))
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)

        response_guest_client = self.guest_client.post(
            reverse(
                "posts:add_comment", args=str(post.pk)), data=form_data,
            follow=True
        )
        comments_count = Comment.objects.count()
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response_guest_client, f"/auth/login/?next=/posts/1/comment/"
        )
