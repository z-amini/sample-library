from rest_framework import routers

from library.books import views

router = routers.DefaultRouter()
router.register(r"tags", views.TagViewSet)
router.register(r"books", views.BookViewSet)
router.register(r"borrows", views.BorrowViewSet)
router.register(r"delay-penalties", views.DelayPenaltyViewSet)
