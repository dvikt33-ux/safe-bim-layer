# APA №2 22Z — контрааудит А: первоисточники/версии/лицензии
Независимая повторная проверка по исходным файлам, не по карточкам №1.

A1. IfcOpenShell закреплён тегом `ifcopenshell-python-0.8.5`; `util/system.py`, `util/cost.py`, `util/sequence.py`, `api/document/*` прочитаны. Сигнатуры newer 0.9 не переносить. LGPL-3.0-or-later подтверждена заголовком `api/document/add_information.py`.
A2. ezdxf закреплён `v1.4.5`; MIT подтверждена `LICENSE`. `recursive_decompose` НЕ делает XCLIP, но `addons/drawing/frontend.py` L882–912 применяет его. `CustomJSONBackend` L172–229 не возвращает исходный handle: исходную привязку не выдумывать.
A3. Graphisoft `archicad-api-devkit` тег `29.3100`: `ACAPI_ProjectOperation_Publish` найден именно в SDK29, а не SDK30. Tapir `1.5.9` подтверждает JSON-контракт, но локальный `1.5.10` нельзя отождествлять по исходникам. Локальная лицензия AC29/MEP не проверялась.
A4. PR173 LIVE-02 — историческая доказательная квитанция по сохранённому снимку; не новый LIVE. Текущий PR HEAD и исполнявшийся commit могут различаться, нужно закреплять оба SHA.
A5. PDF источник и нормативные тексты имеют отдельные права; PyMuPDF может добавлять AGPL/коммерческий риск, но DXF JSONBackend не требует PyMuPDF. Локальные версии, Python imports и Windows wheels в этом цикле не проверялись.

Вердикт: SOURCE VERIFIED по названным файлам; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED новых нет. Никакого benchmark.
