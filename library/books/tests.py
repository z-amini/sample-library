from django.utils import timezone

from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase
from rest_framework.test import APIClient

from library.books.models import Tag, Book, Borrow, DelayPenalty


class BookTestCase(TestCase):
    def create_groups(self):
        managers = Group.objects.create(name="Manager")
        managers.permissions.set(
            Permission.objects.filter(
                codename__in=[
                    "change_borrow",
                    "view_borrow",
                    "add_tag",
                    "change_tag",
                    "delete_tag",
                    "view_tag",
                    "add_book",
                    "change_book",
                    "delete_book",
                    "view_book",
                    "change_delaypenalty",
                    "view_delaypenalty",
                ]
            )
        )
        students = Group.objects.create(name="Student")
        students.permissions.set(
            Permission.objects.filter(
                codename__in=[
                    "add_borrow",
                    "view_borrow",
                    "view_tag",
                    "view_book",
                    "view_delaypenalty",
                ]
            )
        )
        self.groups = [managers, students]

    def create_users(self):
        self.manager = User.objects.create_user(
            "amini", "amini@sharif.edu", "salam*123"
        )
        self.manager.groups.add(self.groups[0])
        self.students = [
            User.objects.create_user(
                "92106345",
                "zamini@ce.sharif.edu",
                "salam*123",
                first_name="Zeynab",
                last_name="Amini",
            ),
            User.objects.create_user(
                "92106215",
                "shirbeigy@ce.sharif.edu",
                "salam*123",
                first_name="Maryam",
                last_name="Shirbeigy",
            ),
        ]
        for student in self.students:
            student.groups.add(self.groups[1])

    def create_books(self):
        self.tags = Tag.objects.bulk_create(
            Tag(name=name) for name in ("Scientific", "General")
        )
        Book.objects.bulk_create(
            Book(**book)
            for book in [
                {
                    "title": "B1",
                    "isbn": "0000000000001",
                    "authors": "A1",
                    "type": "A",
                    "copies": 1,
                },
                {
                    "title": "B2",
                    "isbn": "0000000000002",
                    "authors": "A2, A3",
                    "type": "R",
                    "copies": 2,
                },
                {
                    "title": "B3",
                    "isbn": "0000000000003",
                    "authors": "A3",
                    "type": "T",
                    "copies": 3,
                },
                {
                    "title": "B4",
                    "isbn": "0000000000004",
                    "authors": "A4",
                    "type": "R",
                    "copies": 4,
                },
                {
                    "title": "B5",
                    "isbn": "0000000000005",
                    "authors": "A5, A6",
                    "type": "R",
                    "copies": 5,
                },
            ]
        )
        tags = [(), (1,), (2,), (1, 2), (1, 2)]
        for book in Book.objects.all():
            book.tags.set(tags[book.id - 1])

    def setUp(self):
        self.create_groups()
        self.create_users()
        self.create_books()

    def test_book_view(self):
        """Books are correctly listed"""
        client = APIClient()
        client.login(username=self.students[0].username, password="salam*123")
        response = client.get("/books/")
        json = response.json()
        self.assertEqual(json["count"], 5)

    def test_book_related(self):
        """Related books are correctly identified"""
        client = APIClient()
        client.login(username=self.students[0].username, password="salam*123")
        response = client.get("/books/4/related/")
        json = response.json()
        self.assertEqual(json["count"], 2)
        self.assertEqual(json["results"][0]["id"], 5)
        self.assertEqual(json["results"][1]["id"], 2)

    def test_book_edit_for_manager(self):
        """Manager is allowed to edit"""
        client = APIClient()
        client.login(username=self.manager.username, password="salam*123")
        response = client.get("/books/4/")
        self.assertNotEqual(response.json()["copies"], 2)
        response = client.patch("/books/4/", data={"copies": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["copies"], 2)

    def test_book_edit_for_student(self):
        """Student is prohibited to edit"""
        client = APIClient()
        client.login(username=self.students[0].username, password="salam*123")
        response = client.patch("/books/4/", data={"copies": 2})
        self.assertEqual(response.status_code, 403)

    def test_borrow_request_for_student(self):
        """Student can submit borrow request"""
        client = APIClient()
        client.login(username=self.students[0].username, password="salam*123")
        response = client.post("/borrows/", data={"book": 1})
        self.assertEqual(response.status_code, 201)
        borrow = response.json()
        self.assertEqual(borrow["book"], 1)
        self.assertEqual(borrow["student"], self.students[0].id)
        self.assertIsNotNone(borrow["requested_at"])
        self.assertIsNone(borrow["borrowed_at"])
        self.assertIsNone(borrow["returned_at"])
        self.assertIsNone(borrow["duration"])

    def test_accessible_borrow_list_for_student(self):
        """Student can only view his/her requests"""
        client1 = APIClient()
        client1.login(username=self.students[0].username, password="salam*123")
        client1.post("/borrows/", data={"book": 1})
        client2 = APIClient()
        client2.login(username=self.students[1].username, password="salam*123")
        client2.post("/borrows/", data={"book": 2})
        response = client1.get("/borrows/")
        self.assertEqual(response.json()["count"], 1)
        borrow_id = response.json()["results"][0]["id"]
        borrow = Borrow.objects.get(id=borrow_id)
        self.assertEqual(borrow.student, self.students[0])

    def test_accessible_borrow_list_for_manager(self):
        """Manager can view all requests"""
        client1 = APIClient()
        client1.login(username=self.students[0].username, password="salam*123")
        client1.post("/borrows/", data={"book": 1})
        client2 = APIClient()
        client2.login(username=self.students[1].username, password="salam*123")
        client2.post("/borrows/", data={"book": 2})
        client3 = APIClient()
        client3.login(username=self.manager.username, password="salam*123")
        response = client3.get("/borrows/")
        self.assertEqual(response.json()["count"], 2)

    def test_ran_out_book_for_borrow(self):
        """Book can be borrowed as many times as its copies number"""
        book = Book.objects.get(pk=1)
        self.assertEqual(book.copies, 1)
        client1 = APIClient()
        client1.login(username=self.students[0].username, password="salam*123")
        response = client1.post("/borrows/", data={"book": book.id})
        self.assertEqual(response.status_code, 201)
        client2 = APIClient()
        client2.login(username=self.students[1].username, password="salam*123")
        response = client2.post("/borrows/", data={"book": book.id})
        self.assertEqual(response.status_code, 400)

    def test_book_return_makes_book_available_for_borrow(self):
        """Ran-out book can be borrowed again after returning"""
        book = Book.objects.get(copies=1)
        client1 = APIClient()
        client1.login(username=self.students[0].username, password="salam*123")
        client1.post("/borrows/", data={"book": book.id})
        client2 = APIClient()
        client2.login(username=self.manager.username, password="salam*123")
        client2.post("/borrows/1/start/", data={"duration": 5})
        response = client2.post("/borrows/1/terminate/")
        self.assertIsNotNone(response.json()["returned_at"])
        response = client1.post("/borrows/", data={"book": book.id})
        self.assertEqual(response.status_code, 201)

    def test_concurrent_borrow_for_student(self):
        """Student shall not borrow a book before returning the last one"""
        client = APIClient()
        client.login(username=self.students[0].username, password="salam*123")
        response = client.post("/borrows/", data={"book": 1})
        self.assertEqual(response.status_code, 201)
        response = client.post("/borrows/", data={"book": 2})
        self.assertEqual(response.status_code, 400)

    def test_penalty_is_made_on_delay(self):
        """Delays on returning book must generate penalty"""
        twenty_days_ago = timezone.now() - timezone.timedelta(days=20)
        borrow = Borrow.objects.create(
            book_id=1,
            student=self.students[0],
            requested_at=twenty_days_ago,
            borrowed_at=twenty_days_ago,
            duration=10,
        )
        client = APIClient()
        client.login(username=self.manager.username, password="salam*123")
        client.post("/borrows/1/terminate/", data={"duration": 5})
        borrow.refresh_from_db()
        self.assertIsNotNone(borrow.returned_at)
        self.assertIsNotNone(borrow.delaypenalty)
        self.assertEqual(borrow.delaypenalty.amount, 11 * 1000)

    def test_unpaid_penalty_prevents_borrow(self):
        """Student must pay penalty before borrowing another book"""
        ten_days_ago = timezone.now() - timezone.timedelta(days=10)
        Borrow.objects.create(
            book_id=1,
            student=self.students[0],
            requested_at=ten_days_ago,
            borrowed_at=ten_days_ago,
            duration=6,
        )
        client1 = APIClient()
        client1.login(username=self.manager.username, password="salam*123")
        client1.post("/borrows/1/terminate/")
        client2 = APIClient()
        client2.login(username=self.students[0].username, password="salam*123")
        response = client2.post("/borrows/", data={"book": 5})
        self.assertEqual(response.status_code, 400)
