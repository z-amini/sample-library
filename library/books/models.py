from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("name"))

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def __str__(self):
        return self.name


class Book(models.Model):
    TYPE_RESOURCE = "R"
    TYPE_ARTICLE = "A"
    TYPE_THESIS = "T"
    TYPE_OTHER = "O"
    TYPE_CHOICES = (
        (TYPE_RESOURCE, _("resource")),
        (TYPE_ARTICLE, _("article")),
        (TYPE_THESIS, _("thesis")),
        (TYPE_OTHER, _("other")),
    )

    title = models.CharField(max_length=200, verbose_name=_("title"))
    isbn = models.CharField(
        max_length=13,
        validators=(MinLengthValidator(10),),
        unique=True,
        verbose_name=_("ISBN"),
    )
    authors = models.TextField(verbose_name=_("author(s)"))
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, verbose_name=_("type"))
    tags = models.ManyToManyField(Tag, verbose_name=_("tags"))
    copies = models.PositiveSmallIntegerField(verbose_name=_("number of copies"))

    class Meta:
        verbose_name = _("book")
        verbose_name_plural = _("books")

    def __str__(self):
        return self.title


class Borrow(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"groups__name": "Student"},
        verbose_name=_("student"),
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name=_("book"))
    requested_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("request date")
    )
    borrowed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("borrow date")
    )
    duration = models.DurationField(null=True, blank=True, verbose_name=_("duration"))
    returned_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("return date")
    )

    class Meta:
        verbose_name = _("borrow")
        verbose_name_plural = _("borrows")

    def __str__(self):
        return f"{self.student.get_full_name()}: {self.book}"


class DelayPenalty(models.Model):
    borrow = models.OneToOneField(
        Borrow, on_delete=models.CASCADE, editable=False, verbose_name=_("borrow")
    )
    amount = models.PositiveIntegerField(editable=False, verbose_name=_("amount"))
    is_paid = models.BooleanField(verbose_name=_("is it paid?"))

    class Meta:
        verbose_name = _("delay penalty")
        verbose_name_plural = _("delay  penalties")

    def __str__(self):
        return f"{self.borrow} ({self.amount})"
