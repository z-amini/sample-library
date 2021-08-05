from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from library.books.models import Tag, Book, Borrow, DelayPenalty
from library.books.serializers import (
    TagSerializer,
    BookSerializer,
    DelayPenaltySerializer,
    BorrowSerializer,
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ("name",)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    search_fields = ("title", "isbn", "authors")
    filterset_fields = {
        "type": ["in"],
        "tags": ["in"],
    }

    @method_decorator(cache_page(30 * 60))
    @action(methods=("GET",), detail=True, url_path="related", url_name="related")
    def get_related_books(self, request, *args, **kwargs):
        book = self.get_object()
        page = self.paginate_queryset(book.related_books)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BorrowViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrow.objects.all()
    serializer_class = BorrowSerializer
    search_fields = ("book__title", "student__username")
    filterset_fields = {
        "requested_at": ["lte", "gte"],
    }

    def get_queryset(self):
        if self.request.user.has_perm("books.change_borrow"):
            return self.queryset
        return self.queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(methods=("POST", "PATCH"), detail=True, url_path="start", url_name="start")
    def start_borrow(self, request, *args, **kwargs):
        borrow = self.get_object()
        serializer = self.get_serializer(borrow, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(borrowed_at=timezone.now())
        return Response(serializer.data)

    @action(methods=("POST",), detail=True, url_path="terminate", url_name="terminate")
    def terminate_borrow(self, request, *args, **kwargs):
        borrow = self.get_object()
        borrow.returned_at = timezone.now()
        borrow.save()
        return Response(self.get_serializer(borrow).data)

    def get_serializer_class(self):
        if self.action == "create":
            self.serializer_class.Meta.read_only_fields = (
                "student",
                "borrowed_at",
                "duration",
                "returned_at",
            )
        elif self.action == "start_borrow":
            self.serializer_class.Meta.read_only_fields = (
                "student",
                "book",
                "borrowed_at",
                "returned_at",
            )
        elif self.action == "terminate_borrow":
            self.serializer_class.Meta.read_only_fields = (
                "student",
                "book",
                "borrowed_at",
                "duration",
                "returned_at",
            )
        return self.serializer_class

    def check_permissions(self, request):
        if (
            self.action
            in (
                "start_borrow",
                "terminate_borrow",
            )
            and not request.user.has_perm("books.change_borrow")
        ):
            raise PermissionDenied(_("You may not make this change."))

    def check_object_permissions(self, request, obj):
        if self.action == "start_borrow" and obj.borrowed_at is not None:
            raise PermissionDenied(_("The book is already delivered."))
        if self.action == "terminate_borrow":
            if obj.borrowed_at is None:
                raise PermissionDenied(_("The book is not delivered yet."))
            if obj.returned_at is not None:
                raise PermissionDenied(_("The book is already returned."))


class DelayPenaltyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = DelayPenalty.objects.all()
    serializer_class = DelayPenaltySerializer
    search_fields = ("borrow__book__title", "borrow__student__username")
    filterset_fields = {
        "is_paid": ["exact"],
    }

    def get_queryset(self):
        if self.request.user.has_perm("books.change_delaypenalty"):
            return self.queryset
        return self.queryset.filter(borrow__student=self.request.user)
