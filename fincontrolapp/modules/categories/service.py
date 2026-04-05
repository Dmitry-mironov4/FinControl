from .repository import CategoryRepository


class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    def get_all(self, type_=None):
        return self.repository.get_all(type_=type_)