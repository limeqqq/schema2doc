# schema2doc

**Zero-Dependency SQLite Schema to Markdown & Mermaid Documentation Generator**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-green.svg)](https://pypi.org/project/schema2doc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-14%20passed-brightgreen.svg)](#testing)

[English](README.md) | [Русский](README.ru.md)

---

## Overview

**schema2doc** is a zero-dependency Python CLI tool designed for automated **SQLite** schema introspection and technical documentation generation. It inspects local SQLite databases using low-level PRAGMA statements and produces self-contained Markdown specifications featuring interactive **Mermaid.js** Entity-Relationship diagrams.

### Supported DBMS

* **SQLite 3** (`.db`, `.sqlite`, `.sqlite3`) — native introspection via system PRAGMA commands (`table_info`, `foreign_key_list`, `index_list`).
* *(Modular inspector architecture designed for straightforward extensions like DuckDB or PostgreSQL.)*

### Key Architectural Highlights

* **Zero Dependencies:** Built entirely on Python 3.10+ standard libraries (`sqlite3`, `dataclasses`, `argparse`). No heavy external dependencies, no JVM, and no Graphviz installation required.
* **Zero-Read Data Privacy:** Queries only schema catalog metadata without reading table rows. Completely safe to run against production database dumps.
* **Native Markdown & Mermaid:** Outputs clean, GitHub-flavored Markdown tables and standards-compliant Mermaid ERDs that render natively in GitHub, GitLab, Obsidian, and VS Code.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/limeqqq/schema2doc.git
cd schema2doc

# Generate schema documentation for the demo database
python -m schema2doc examples/ecommerce.db -o SCHEMA.md
```

---

## AI-Assisted Engineering Workflow

This project was architected and built using test-driven, agent-assisted workflows. A detailed case study covering prompt engineering, architectural decisions, and agent collaboration with OpenCode is documented in [AI_WORKFLOW.md](AI_WORKFLOW.md).

## Testing

Run the test suite using standard Python unittest:

```bash
python -m unittest discover tests
```

Includes 14 unit tests covering DTO mappings, composite key parsing (PK/FK), Mermaid ERD syntax compliance, and database error boundaries.

## License

MIT License. See [LICENSE](LICENSE) for details.