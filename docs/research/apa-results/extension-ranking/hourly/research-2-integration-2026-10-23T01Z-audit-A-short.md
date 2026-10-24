# APA №2 — контрааудит А, 01Z

Статическое сопоставление PR74, PR149, PR162 и закреплённой схемы Tapir. Без запуска.

- CreateSlabs v1.0.3 допускает favoriteName, но не material/structure; PR162 compiler не передаёт favoriteName.
- ModifySlabs v1.4.0 допускает material/structure; существующий SceneWriter делает Create→GUID→Modify с записью SQLite перед изменением.
- У второй мутации используется исходная запись разрешения CreateSlabs. Требуется аудит составного разрешения; нарушение не доказано.
- Ограничение floor0 в PR149 относится к узкому verifier, не ко всей схеме ModifySlabs.

G2 SOURCE_ONLY. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
