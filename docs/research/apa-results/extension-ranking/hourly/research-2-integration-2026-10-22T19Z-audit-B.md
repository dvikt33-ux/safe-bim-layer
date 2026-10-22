# APA №2 — контрааудит Б, SOURCE

B1: BIM Graph знает CreateBeams, SceneWriter требует opt-in adapter. Beam optional.

B2: PR126 batch 1–200 GUID против PR74 created_guid одного элемента. Для BUILD-01 single-create.

B3: GetAllElements текущей базы не гарантирует два этажа. GetModelDumpV1 есть в source, установленная регистрация не доказана. BREP после Save/Close/Reopen не принят.

B4: исторический 21-элементный прототип PR74 и scratch PR159 не являются новым BUILD-01. Повтор CREATE после UNKNOWN запрещён.

Итог SOURCE_ONLY; G0 BLOCKED; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
