  3     Ниже представлена предварительная схема связей и структур
          двух репозиториев.
    4
    5         "pr-sync (Automation Toolkit)" │ "oracle-capacity-
    ⋮     hunter-claude"
    ⋮
    ⋮         ┌─────────────────┐    ┌────────┐    ┌────────┐
    ⋮     ┌─────────────────────┐
    ⋮         │ .github/agents/ │    │ tests/ │    │ tests/ │    │
    ⋮     config.example.yaml │
    ⋮         └─────────────────┘    └────────┘    └────────┘
    ⋮     └─────────────────────┘
    ⋮                  │ SDD Workflows                       │ Tests
    ⋮     │ Configuration
    ⋮                  ▼                                ▼
    ⋮     ▼
    ⋮         ┌───────────┐    ┌──────┐
    ⋮         │ .specify/ │    │ src/ │
    ⋮         └───────────┘    └──────┘
    ⋮               │ Constitution & Specs        │ Перенос и
    ⋮     генерализация логики
    ⋮               ▼              ▼
    ⋮         ┌──────┐
    ⋮         │ src/ │
    ⋮         └──────┘
    ⋮
    ⋮         PR_TESTS ──Spec-backed tests──► PR_SRC
    ⋮
   37     ## Анализ переносимой логики