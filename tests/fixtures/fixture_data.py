import pytest
from posts.models import Group, Post


@pytest.fixture
def post(user):
    return Post.objects.create(text='Тестовый пост 1', author=user)


@pytest.fixture
def group():
    return Group.objects.create(title='Тестовая группа 1', slug='test-link', description='Тестовое описание группы')


@pytest.fixture
def post_with_group(user, group):
    return Post.objects.create(text='Тестовый пост 2', author=user, group=group)
