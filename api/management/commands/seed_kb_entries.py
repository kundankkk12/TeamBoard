from django.core.management.base import BaseCommand

from api.models import KBEntry


SEED_ENTRIES = [
    {
        'question': 'What is select_related in Django ORM?',
        'answer': 'select_related performs a SQL JOIN and fetches related objects in one query.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'When should I use prefetch_related?',
        'answer': 'Use prefetch_related for many-to-many and reverse foreign key lookups.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'How does transaction.atomic() work in Django?',
        'answer': 'transaction.atomic() wraps operations in a single database transaction block.',
        'category': KBEntry.Category.FRAMEWORK,
    },
    {
        'question': 'What is a JWT token?',
        'answer': 'JWT is a compact token format used for stateless API authentication.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'How do Q objects help in filtering?',
        'answer': 'Q objects allow complex OR/AND conditions in Django queryset filters.',
        'category': KBEntry.Category.FRAMEWORK,
    },
    {
        'question': 'How do I secure REST APIs?',
        'answer': 'Use authentication, authorization, input validation, and HTTPS for API security.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'What is horizontal scaling in cloud systems?',
        'answer': 'Horizontal scaling adds more instances behind a load balancer to handle traffic.',
        'category': KBEntry.Category.CLOUD,
    },
    {
        'question': 'What is connection pooling in databases?',
        'answer': 'Connection pooling reuses open database connections to reduce overhead.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'How do retries improve API reliability?',
        'answer': 'Retries with backoff can recover from transient network and service failures.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'What is idempotency in API design?',
        'answer': 'An idempotent request can be repeated safely without changing the result.',
        'category': KBEntry.Category.GENERAL,
    },
    {
        'question': 'How should I monitor cloud infrastructure?',
        'answer': 'Track latency, error rates, saturation, and resource metrics with alerts.',
        'category': KBEntry.Category.CLOUD,
    },
    {
        'question': 'How can I optimize slow ORM queries?',
        'answer': 'Use select_related, prefetch_related, indexing, and query profiling tools.',
        'category': KBEntry.Category.DATABASE,
    },
]


class Command(BaseCommand):
    help = 'Seed at least 10 KB entries with mixed categories and reusable keywords.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing KBEntry records before seeding.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted_count, _ = KBEntry.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing KB entries.'))

        created_count = 0
        for entry in SEED_ENTRIES:
            _, created = KBEntry.objects.get_or_create(
                question=entry['question'],
                defaults={
                    'answer': entry['answer'],
                    'category': entry['category'],
                },
            )
            if created:
                created_count += 1

        total_count = KBEntry.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Inserted {created_count} entries. Total KB entries: {total_count}.'))
