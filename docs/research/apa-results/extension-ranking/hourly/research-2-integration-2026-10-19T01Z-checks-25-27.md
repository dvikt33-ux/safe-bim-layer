# APA №2 01Z — проверки 25–27: Hotlink evidence
APA PR173 head eee149369e9f4bec44ba176d13daf2c07558ce92.
S1 https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/receipt.json
S2 https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/apa_ac29_hotlink_batch_geometry.py

25. Вопрос: был ли native batch? S1:2–47: 69→119 GUID, 2 instances, 48 children, nativeBatchCalls=1, saveCalls=1, reopenVerified=true; это опубликованная LIVE квитанция, не запуск этого цикла. Далее координаты.
26. Вопрос: универсальна ли геометрия? S2:98–129 `origin_x=right+gap-local_min_x`, только rotation=0, mirror=false, same story. Не переносить на поворот/зеркало. Далее приёмка.
27. Вопрос: ACCEPTED? S1:63–64 `originalBatchScratchAccepted=false`, `originalBatchScratchDriftPreserved=true`. Сохранение и reopen не равны итоговой независимой приёмке. NO REPLAY. Далее 4D.
