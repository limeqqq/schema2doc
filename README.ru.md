# schema2doc

**Генератор документации схемы SQLite на Markdown и Mermaid без внешних зависимостей**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-green.svg)](https://pypi.org/project/schema2doc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/limeqqq/schema2doc/actions/workflows/tests.yml/badge.svg)](https://github.com/limeqqq/schema2doc/actions/workflows/tests.yml)

[English](README.md) | [Русский](README.ru.md)

---

## Обзор

**schema2doc** — это утилита CLI на Python с нулевыми внешними зависимостями, предназначенная для автоматизированной интроспекции схемы **SQLite** и генерации технической документации. Инструмент инспектирует локальные базы данных SQLite с помощью системных команд PRAGMA и формирует автономные Markdown-спецификации с интерактивными ER-диаграммами **Mermaid.js**.

### Поддерживаемые СУБД

* **SQLite 3** (`.db`, `.sqlite`, `.sqlite3`) — нативная интроспекция через системные команды PRAGMA (`table_info`, `foreign_key_list`, `index_list`).
* *(Модульная архитектура инспектора предназначена для простого расширения до DuckDB или PostgreSQL.)*

### Ключевые архитектурные особенности

* **Zero Dependencies:** Построен исключительно на стандартных библиотеках Python 3.10+ (`sqlite3`, `dataclasses`, `argparse`). Aucun внешних зависимостей, нет JVM, не требуется установка Graphviz.
* **Zero-Read политика безопасности:** Запросы затрагивают только метаданные каталога схемы без чтения строк таблиц. Полностью безопасно для запуска против рабочих дампов баз данных.
* **Нативный Markdown и Mermaid:** Выводит чистые таблицы GitHub-flavored Markdown и соответствующие стандартам Mermaid ERD, которые отображаются нативно в GitHub, GitLab, Obsidian и VS Code.

---

## Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/limeqqq/schema2doc.git
cd schema2doc

# Генерация документации схемы для демо-базы
python -m schema2doc examples/ecommerce.db -o SCHEMA.md
```

---

## Рабочий процесс с ИИ-ассистентом

Проект был спроектирован и создан с использованием тестируемо-ориентированных, ассистент-опекаемых workflow. Подробное кейс-исследование, охватывающее инженерию промптов, архитектурные решения и взаимодействие с агентом OpenCode, задокументировано в [AI_WORKFLOW.md](AI_WORKFLOW.md).

## Тестирование

Запустите набор тестов с помощью стандартного Python unittest:

```bash
python -m unittest discover tests
```

Включает 14 юнит-тестов, охватывающих отображение DTO, парсинг комбинированных ключей (PK/FK), соответствие синтаксису Mermaid ERD и границы обработки ошибок базы данных.

## Лицензия

Лицензия MIT. Подробности в файле [LICENSE](LICENSE).