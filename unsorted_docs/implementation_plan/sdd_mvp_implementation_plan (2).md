## Goal Description
Завершить стадию MVP для обоих проектов (`pr-sync` и `oracle-capacity-hunter-claude`), формализовать оставшиеся артефакты Spec-Driven Development (SDD) и зафиксировать четкую архитектуру. Это позволит закрыть текущий этап (MVP) без задержек и перерасхода ресурсов на сложную LLM-генерацию.

## User Review Required
> [!IMPORTANT]
> **Архитектурный перенос:** Как мы выяснили ранее, в репозитории `oracle-capacity-hunter-claude` **нет** логики генерации PR-описаний. Поэтому "перенос логики автоматизации написания PR" из него невозможен. 
> В рамках этого плана мы зафиксируем архитектуру обоих проектов в виде Mermaid-диаграмм в папках `docs/`, чтобы вы могли наглядно убедиться в этом и закрыть вопросы по MVP. Согласны ли вы с таким подходом?

## Open Questions
- Хотите ли вы, чтобы в рамках этого плана мы также рефакторили `pr-sync` для использования паттерна `config.py` (как в Oracle-боте), или для выпуска MVP достаточно просто задокументировать текущую архитектуру обоих проектов в `docs/`?

## Proposed Changes

### Component: pr-sync (Automation Toolkit)
Добавление финальных артефактов SDD для завершения Phase 2 (Implementation & Analyze).
#### [NEW] `prepared_docs/analyze-pr-sync.md`
- Создание отчета о кросс-артефактном анализе и покрытии инвариантов.
- Фиксация решения о заморозке LLM-интеграции (v1.1+) для предотвращения перерасхода ресурсов.
#### [NEW] `prepared_docs/architecture.md`
- Добавление Mermaid-диаграмм структуры `src/toolkit` и процесса Gitflow + роли агентов.

### Component: oracle-capacity-hunter-claude
Фиксация архитектуры бота для четкого понимания его структуры и границ.
#### [NEW] `docs/architecture.md`
- Добавление Mermaid-диаграммы структуры бота (CLI -> Config -> Finder -> Notifier).

## Verification Plan
### Manual Verification
1. Открыть сгенерированные файлы `architecture.md` в IDE (Cursor/VS Code) или на GitHub.
2. Убедиться, что Mermaid-диаграммы корректно рендерятся.
3. Проверить отчет `analyze-pr-sync.md` на соответствие стандартам SDD.
