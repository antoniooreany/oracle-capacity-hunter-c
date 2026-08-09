1      Automation Toolkit: Architecture & Process
    2
    3     ## 1. Архитектура Automation Toolkit (pr-sync)
    5
    6     Минимальная схема, показывающая объединение универсальной
    ⋮     логики (движков) и специфичных SDD инструментов.
    ⋮
    ⋮         "Automation Toolkit (Core)" │ "Tools (CLI / Actions)"
    ⋮     │ "Legacy (oracle-capacity-hunter-claude)"
    ⋮
    ⋮         ┌───────────────┐    ┌───────────────────────────┐
    ⋮         │ State Manager │    │ Business Logic / Scraping │
    ⋮         └───────────────┘    └───────────────────────────┘
    ⋮                                            │ Генерализация
    ⋮                                            ▼
    ⋮         ┌───────────────────┐    ┌───────────────────┐
    ⋮         │ GitHub API Client │    │ Text / AST Parser │
    ⋮         └───────────────────┘    └───────────────────┘
    ⋮                   │                        │
    ⋮                   ▼                        ▼
    ⋮         ┌─────────────────────────────────┐
    ⋮     ┌─────────────────────────┐    ┌────────────────────────┐
    ⋮         │ pr-sync: PR Autogeneration v1.0 │    │ doc-sync:
    ⋮     Documentation │    │ release-sync: Releases │
    ⋮         └─────────────────────────────────┘
    ⋮     └─────────────────────────┘    └────────────────────────┘
    ⋮
    ⋮         CORE_STATE ──► TOOL_PR
    ⋮       ──────
   41     ## 2. Процесс Gitflow и Роли Агентов