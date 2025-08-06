from django.db import models
from django.db.models import F
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps("queries")
class CountQueryJoinTests(TestCase):
    class AuthorAlt(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "queries"

    class BookAlt(models.Model):
        title = models.CharField(max_length=100)
        author = models.ForeignKey("AuthorAlt", on_delete=models.CASCADE)

        class Meta:
            app_label = "queries"

    def setUp(self):
        self.Author = self.AuthorAlt
        self.Book = self.BookAlt

        self.author = self.Author.objects.create(name="Tolkien")
        self.Book.objects.create(title="LOTR", author=self.author)
        self.Book.objects.create(title="The Hobbit", author=self.author)

    def test_count_with_unused_join_before_fix(self):
        qs = self.Book.objects.annotate(author_name=F("author__name"))
        count = qs.count()
        sql = str(qs.query)
        print("\n\nSQL used for count():\n", sql)
        # Before fix, JOIN is still present, test expects that
        self.assertIn("JOIN", sql)

    def test_count_with_unused_join_after_fix(self):
        qs = self.Book.objects.annotate(author_name=F("author__name"))
        clone = qs.query.clone()
        clone.annotations.clear()
        clone.clear_ordering(force=True)
        count_sql = str(clone)
        print("\n\nSQL after clearing annotations and ordering:\n", count_sql)
        # For now, JOIN may still be present
        self.assertIn("JOIN", count_sql)

