from django.contrib import admin

from library.books.models import Tag, Book, Borrow, DelayPenalty


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "isbn", "authors")
    list_filter = ("type", "tags")
    search_fields = ("title", "isbn", "authors")


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ("book", "student", "requested_at", "borrowed_at", "returned_at")
    list_filter = ("requested_at", "borrowed_at")
    search_fields = ("book__title", "book__isbn", "student__username")
    raw_id_fields = ("book", "student")


@admin.register(DelayPenalty)
class DelayPenaltyAdmin(admin.ModelAdmin):
    list_display = ("borrow", "amount", "is_paid")
    list_filter = ("is_paid",)
    search_fields = (
        "borrow__book__title",
        "borrow__book__isbn",
        "borrow__student__username",
    )
    raw_id_fields = ("borrow",)

    def has_add_permission(self, request):
        return False
