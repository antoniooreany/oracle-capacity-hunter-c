1      Архитектура и связи сущностей: oracle-capacity-hunter и
          pr-sync
    2
    3     Это профессиональная диаграмма, построенная с помощью
          Mermaid.js (индустриальный стандарт "Docs-as-Code" для
          архитектуры). Вы можете просматривать ее прямо здесь или
          вставить в любой Markdown-файл, поддерживающий Mermaid
          (включая GitHub).
    4
    5     ## 1. pr-sync (Целевой проект — Генерализированная логика)
    6
    7     Структура нового инструмента, который должен стать
          универсальным CLI-решением для создания PR в любых
          репозиториях.
    8
    9         📊 Diagram (unsupported type)
    ⋮         ──────────────────────────────
    ⋮         classDiagram
    ⋮             direction TB
    ⋮             class CLI {
>   ⋮                 +main()
    ⋮                 -parse_args()
    ⋮             }
    ⋮             class GitHubAPI {
    ⋮                 <<gh_api.py>>
    ⋮                 +check_auth()
    ⋮                 +find_open_pr()
    ⋮                 +create_pr()
    ⋮                 +update_pr()
    ⋮             }
    ⋮             class GitAPI {
  [0%  L9  1-31/111]
