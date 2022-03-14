from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст", blank=False)
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата публикации",
        help_text="Дата публикации нового поста",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
        help_text="Автор нового поста",
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="группа",
        help_text="Группа для нового поста",
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        count_symbol = 15
        return self.text[:count_symbol]

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"post_id": self.pk})


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Комментарий",
        help_text="Текст комментария",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
        help_text="Автор нового поста",
    )

    text = models.TextField()
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата размещения",
        help_text="Дата размещения комментария",
    )

    def __str__(self):
        count_symbol = 15
        return self.text[:count_symbol]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
        help_text="Пользователь, который подписывается",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
        help_text="Автор, на которого подписываются",
    )

    def __str__(self):
        return self.user
