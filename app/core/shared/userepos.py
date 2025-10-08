# مثال استفاده
from app.core.shared.database import get_db
from app.core.shared.repositories import get_repository_factory

def example_usage():
    db = next(get_db())
    repo_factory = get_repository_factory(db)
    
    # استفاده از ریپازیتوری مشتریان
    customer_repo = repo_factory.customers
    new_customer = customer_repo.create({
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe'
    })
    
    # استفاده از ریپازیتوری دامنه‌ها
    domain_repo = repo_factory.domains
    domains = domain_repo.get_customer_domains(new_customer.id)
    
    # استفاده از آمار
    stats = repo_factory.stats.get_system_stats()
    print(f"Total customers: {stats['total_customers']}")