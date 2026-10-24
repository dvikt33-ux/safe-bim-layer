# APA №1 21Z — контрааудит А: первоисточники, версии, лицензии

1. Канонический PROJECT_PLAN.json прочитан в ветке research/apa-verified-results-hub-20261010: blob c2ab2f9d, revision182, 91 task. Прочитаны NEXT_RESEARCH_PRIORITIES.md, реестр 61, аудит №3 20Z, отчёт №2 20Z, PR154/165/170/171/173.
2. IfcOpenShell: индекс поисковика может показывать 0.8.5, но live docs уже 0.9.0post1. Поэтому прочитан tag ifcopenshell-python-0.8.5 commit 16723d11 и точные строки исходников. PyPI 0.8.5 Win64 wheel SHA подтверждён, но wheel→tag reproducibility и локальный runtime NOT_VERIFIED.
3. ezdxf: прочитан tag v1.4.5 commit 84ae3197, LICENSE MIT, PyPI Python>=3.11; stable docs 1.4.4 не подменяют версию 1.4.5.
4. AC29 MEP licensing нельзя выводить из AC28: 29 требует Collaborate для MEP Designer и cloud license для расчётов; entitlement конкретного пользователя NOT_VERIFIED.
5. PyMuPDF имеет AGPLv3/commercial, не MIT. IfcOpenShell LGPL-3.0-or-later, ezdxf MIT. Права на нормативную XML ФГИС ЦС не установлены, официальный fetch 403.
6. Использован ChatGPT web browser по просьбе пользователя + GitHub connector; Opera в этом цикле НЕ проверялась (NOT_VERIFIED). Ни один SOURCE вывод не повышен до LIVE.

Вердикт: SOURCE_PARTIAL_VERIFIED; OFFLINE/BUILD/INSTALLED/LIVE=NOT_RUN/NOT_CHECKED; ACCEPTED=NO.