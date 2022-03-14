from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    COUNT_SYMBOL = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Пробный текст для тестирования",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        post = PostModelTest.post
        group = PostModelTest.group
        method_str = (
            (str(post), post.text[: self.COUNT_SYMBOL]),
            (str(group), group.title),
        )
        for value, expected in method_str:
            with self.subTest(value=value):
                self.assertEqual(value, expected)
