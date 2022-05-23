import re

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.db.models import fields
from django.template.loader import get_template, select_template

try:
    from posts.models import Post
except ImportError:
    assert False, 'Не найдена модель Post'

try:
    from posts.models import Group
except ImportError:
    assert False, 'Не найдена модель Group'


def search_field(fields, attname):
    for field in fields:
        if attname == field.attname:
            return field
    return None


def search_refind(execution, user_code):
    """Поиск запуска"""
    for temp_line in user_code.split('\n'):
        if re.search(execution, temp_line):
            return True
    return False


class TestPost:

    @pytest.mark.django_db(transaction=True)
    def test_index_view(self, client, post_with_group):
        try:
            response = client.get('/')
        except Exception as e:
            assert False, f'''Главная страница работает неправильно. Ошибка: `{e}`'''
        assert response.status_code != 404, (
            'Главная страница не найдена, проверьте этот адрес в *urls.py*'
        )
        assert response.status_code != 500, (
            'Главная страница не работает. Проверьте ее view-функцию'
        )
        assert response.status_code == 200, (
            'Главная страница работает неправильно.'
        )
        # проверка моделей
        response_text = response.content.decode()
        posts = Post.objects.all()
        for p in posts:
            assert p.text in response_text, (
                'Убедитесь, что на главной странице выводятся все посты '
                'с сортировкой по убыванию даты публикации'
            )

    def test_post_model(self):
        model_fields = Post._meta.fields
        text_field = search_field(model_fields, 'text')
        assert text_field is not None, 'Добавьте название события `text` модели `Post`'
        assert type(text_field) == fields.TextField, (
            'Свойство `text` модели `Post` должно быть текстовым `TextField`'
        )

        pub_date_field = search_field(model_fields, 'pub_date')
        assert pub_date_field is not None, 'Добавьте дату и время проведения события `pub_date` модели `Post`'
        assert type(pub_date_field) == fields.DateTimeField, (
            'Свойство `pub_date` модели `Post` должно быть датой и время `DateTimeField`'
        )
        assert pub_date_field.auto_now_add, 'Свойство `pub_date` модели `Post` должно быть `auto_now_add`'

        author_field = search_field(model_fields, 'author_id')
        assert author_field is not None, 'Добавьте пользователя, автор который создал событие `author` модели `Post`'
        assert type(author_field) == fields.related.ForeignKey, (
            'Свойство `author` модели `Post` должно быть ссылкой на другую модель `ForeignKey`'
        )
        assert author_field.related_model == get_user_model(), (
            'Свойство `author` модели `Post` должно быть ссылкой на модель пользователя `User`'
        )

        group_field = search_field(model_fields, 'group_id')
        assert group_field is not None, 'Добавьте свойство `group` в модель `Post`'
        assert type(group_field) == fields.related.ForeignKey, (
            'Свойство `group` модели `Post` должно быть ссылкой на другую модель `ForeignKey`'
        )
        assert group_field.related_model == Group, (
            'Свойство `group` модели `Post` должно быть ссылкой на модель `Group`'
        )
        assert group_field.blank, (
            'Свойство `group` модели `Post` должно быть с атрибутом `blank=True`'
        )
        assert group_field.null, (
            'Свойство `group` модели `Post` должно быть с атрибутом `null=True`'
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_create(self, user):
        text = 'Тестовый пост'
        author = user

        assert Post.objects.all().count() == 0

        post = Post.objects.create(text=text, author=author)
        assert Post.objects.all().count() == 1
        assert Post.objects.get(text=text, author=author).pk == post.pk

    def test_post_admin(self):
        admin_site = site

        assert Post in admin_site._registry, 'Зарегестрируйте модель `Post` в админской панели'

        admin_model = admin_site._registry[Post]

        assert 'text' in admin_model.list_display, (
            'Добавьте `text` для отображения в списке модели административного сайта'
        )
        assert 'pub_date' in admin_model.list_display, (
            'Добавьте `pub_date` для отображения в списке модели административного сайта'
        )
        assert 'author' in admin_model.list_display, (
            'Добавьте `author` для отображения в списке модели административного сайта'
        )
        assert 'group' in admin_model.list_display, (
            'Добавьте `group` для отображения в списке модели административного сайта'
        )
        assert 'pk' in admin_model.list_display, (
            'Добавьте `pk` для отображения в списке модели административного сайта'
        )
        assert 'text' in admin_model.search_fields, (
            'Добавьте `text` для поиска модели административного сайта'
        )

        assert 'group' in admin_model.list_editable, (
            'Добавьте `group` в поля доступные для редактирования в модели административного сайта'
        )

        assert 'pub_date' in admin_model.list_filter, (
            'Добавьте `pub_date` для фильтрации модели административного сайта'
        )

        assert hasattr(admin_model, 'empty_value_display'), (
            'Добавьте дефолтное значение `-пусто-` для пустого поля'
        )
        assert admin_model.empty_value_display == '-пусто-', (
            'Добавьте дефолтное значение `-пусто-` для пустого поля'
        )


class TestGroup:

    def test_group_model(self):
        model_fields = Group._meta.fields
        title_field = search_field(model_fields, 'title')
        assert title_field is not None, 'Добавьте название события `title` модели `Group`'
        assert type(title_field) == fields.CharField, (
            'Свойство `title` модели `Group` должно быть символьным `CharField`'
        )
        assert title_field.max_length == 200, 'Задайте максимальную длину `title` модели `Group` 200'

        slug_field = search_field(model_fields, 'slug')
        assert slug_field is not None, 'Добавьте уникальный адрес группы `slug` модели `Group`'
        assert type(slug_field) == fields.SlugField, (
            'Свойство `slug` модели `Group` должно быть `SlugField`'
        )
        assert slug_field.unique, 'Свойство `slug` модели `Group` должно быть уникальным'

        description_field = search_field(model_fields, 'description')
        assert description_field is not None, 'Добавьте описание `description` модели `Group`'
        assert type(description_field) == fields.TextField, (
            'Свойство `description` модели `Group` должно быть текстовым `TextField`'
        )

    @pytest.mark.django_db(transaction=True)
    def test_group_create(self, user):
        text = 'Тестовый пост'
        author = user

        assert Post.objects.all().count() == 0

        post = Post.objects.create(text=text, author=author)
        assert Post.objects.all().count() == 1
        assert Post.objects.get(text=text, author=author).pk == post.pk

        title = 'Тестовая группа'
        slug = 'test-link'
        description = 'Тестовое описание группы'

        assert Group.objects.all().count() == 0
        group = Group.objects.create(title=title, slug=slug, description=description)
        assert Group.objects.all().count() == 1
        assert Group.objects.get(slug=slug).pk == group.pk

        post.group = group
        post.save()
        assert Post.objects.get(text=text, author=author).group == group


class TestGroupView:

    @pytest.mark.django_db(transaction=True)
    def test_group_view(self, client, post_with_group):
        try:
            response = client.get(f'/group/{post_with_group.group.slug}')
        except Exception as e:
            assert False, f'''Страница `/group/<slug>/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = client.get(f'/group/{post_with_group.group.slug}/')
        if response.status_code == 404:
            assert False, 'Страница `/group/<slug>/` не найдена, проверьте этот адрес в *urls.py*'

        if response.status_code != 200:
            assert False, 'Страница `/group/<slug>/` работает неправильно.'
        group = post_with_group.group
        html = response.content.decode()

        templates_list = ['group_list.html', 'posts/group_list.html']
        html_template = select_template(templates_list).template.source

        assert search_refind(r'{%\s*for\s+.+in.*%}', html_template), (
            'Отредактируйте HTML-шаблон, используйте тег цикла'
        )
        assert search_refind(r'{%\s*endfor\s*%}', html_template), (
            'Отредактируйте HTML-шаблон, не найден тег закрытия цикла'
        )

        assert re.search(
            r'<\s*p(\s+class=".+"|\s*)>\s*' + post_with_group.text + r'\s*<\s*\/p\s*>',
            html
        ), 'Отредактируйте HTML-шаблон, не найден текст поста `<p>{{ текст_поста }}</p>`'

        assert re.search(
            r'(д|Д)ата публикации:\s*',
            html
        ), (
            'Отредактируйте HTML-шаблон, не найдена дата публикации '
            '`дата публикации: {{ дата_публикации|date:"d E Y" }}`'
        )

        assert re.search(
            r'(а|А)втор\:\s' + post_with_group.author.get_full_name(),
            html,
        ), (
            'Отредактируйте HTML-шаблон, не найден автор публикации '
            '`Автор: {{ полное_имя_автора_поста }},`'
        )

        base_template = get_template('base.html').template.source
        assert re.search(
            r'{\%\sload static\s\%}', base_template
        ), 'Загрузите статику в base.html шаблоне'
