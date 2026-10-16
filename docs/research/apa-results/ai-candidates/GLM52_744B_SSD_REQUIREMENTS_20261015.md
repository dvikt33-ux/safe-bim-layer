# APA — SSD под GLM-5.2 744B в Colibrì: технические требования и варианты покупки

**Дата:** 2026-10-15. **Статус:** SOURCE_VERIFIED, NOT_BENCHMARKED_ON_USER_PC, NO_PURCHASE, NO_INSTALLATION.
**Оборудование:** Lenovo Legion Pro 5 16ARX8/Type 82WM, Ryzen 9 7945HX, RTX 4060 Laptop 8GB VRAM, 48GB RAM, 1TB current YMTC system NVMe. Второй **M.2 2280 PCIe 4.0 x4** слот подтверждён в Lenovo PSREF: https://psref.lenovo.com/syspool/Sys/PDF/Legion/Legion_Pro_5_16ARX8/Legion_Pro_5_16ARX8_Spec.PDF . Lenovo «up to 1 TB» в PSREF относится к протестированным заводским конфигурациям, не к доказанному потолку контроллера. Требование к покупке: второй низкопрофильный M.2 2280 NVMe **без высокого радиатора**.

## GLM-5.2 744B и 1TB

- Текущий README upstream Colibrì https://github.com/JustVugg/colibri — **GLM-5.2 744B / ~40B active**, вес **429GB int4-g64** (готовый с Hugging Face, без FP8-конвертации). Для него физически хватит выделенного 1TB (nominal 1000GB = 931GiB в Windows). Остаток около 571GB decimal до других файлов и служебного места.
- https://huggingface.co/mastouri/GLM-5.2-colibri-E8-IQ3-with-int8-mtp — альтернативный community quant 289.1GB, claimed ~22–33% speed boost on a DIFFERENT RTX5080 16GB/128GB RAM Windows machine, source card quality tests vendor-reported only. Не считать эквивалентным оригинальному INT4 без проверки.
- Хранение готовой Q4-копии **не равно полной локальной конвертации**: FP8-веса (~744GB+), INT4 output (~429GB) и промежуточные слои совместно могут превысить 1TB. На 1TB использовать заранее подготовленные веса, checksum revision pinned; не скачивать FP8 и не конвертировать на этом же диске без отдельного свободного места.
- Это **read-heavy streaming**, ~11GB cold expert reads/token, примерно 19 MB expert chunks, не маленький 4K IOPS workload. Критически важны random/mixed reads с крупными блоками, sustained throughput, thermal throttle, а не только 7400MB/s реклама. TBW — запись; систематическое **чтение** само по себе почти не расходует TBW. Swap writes при недостатке RAM, однако, расходуют ресурс.
- Нормативные benchmark Colibrì: https://github.com/JustVugg/colibri/blob/main/docs/benchmarks.md ; cold 0.05–0.1 tok/s на исходном разработческом 25GB RAM / slow NVMe. «Native PCIe4 32GB RAM ~0.5–1tok/s» — **прогноз автора, не измерение**. Примеры у 128GB RAM достигают 1+ tok/s на *другом* оборудовании; не обещать токены/сек на Lenovo 48GB.
- Есть `iobench` Colibrì: **8 параллельных чтений по 19 MB**, buffered и O_DIRECT для настоящего дискового чтения. Тестировать с новым шардом, не путать OS page-cache с реальной скоростью SSD.
- Источник RAM: dense ~9.9 GB, остальное кэш экспертов; Archicad/Windows должны оставить headroom. GPU 8GB не загружает всю 744B, в Colibri есть Vulkan/offload tier, но **не подтверждено** фактическое ускорение на этом ноутбуке.

## Кандидаты РФ с проверкой страницы 2026-10-15

| Модель (точный SKU) | Продавец / доказательство цены/наличия | Цена на странице | Существенное | Осталось подтвердить |
|---|---|---|---|---|
| **ADATA LEGEND 960 1TB, ALEG-960-1TCS** | https://kazan.xcom-shop.ru/adata_aleg-960-1tcs_988692.html : **в наличии 4–20**, передача в транспортную компанию 19.10 | **18 466 ₽** (другая строка 19 325 ₽, оформление может зависеть от способов оплаты) | TLC, DRAM 1GB, SM2264, PCIe4 x4, до 7400MB/s; TBW 780TB. В комплекте возможен низкопрофильный НЕустановленный радиатор — сверить фактическую толщину и не ставить тяжёлый радиатор в ноутбук. | Доставка в **Кострому** и итог ≤25 000 ₽ не посчитаны; продавец на странице пишет 12 мес. гарантия, а не 5 лет производителя |
| **WD Black SN850X 1TB WDS100T2X0E** (обязательно X0E, НЕ XHE) | https://28bit.ru/tverdotelnyy-nakopitel-western-digital-1000-gb-black-wds100t2x0e/ : 2026-10-15 **в наличии** | **19 990 ₽** | TLC PCIe4 x4, до 7300MB/s, без радиатора, DRAM, TBW 600TB; хороший класс для sustained reads | Доставка до Костромы и окончательная сумма не рассчитаны; у магазина указано 12 мес. гарантии |
| **WD Black SN7100 1TB WDS100T4X0E** | https://28bit.ru/tverdotelnyy-nakopitel-western-digital-1000-gb-sn7100-black-wds100t4x0e/ : **НЕТ В НАЛИЧИИ** на 2026-10-15 | Цену как покупаемую **не указывать** | TLC, DRAM-less/HMB, эффективный ноутбучный PCIe4, до 7250MB/s | Не предлагать купить из отсутствующей карточки |
| **WD Black SN850X 1TB WDS100T2XHE** | https://kostroma.garage812.com/ssd-nakopitel-western-digital-wd-black-sn850x-nvme-1tb-wds100t2xhe/ : 1 шт, ~19 990 ₽ | **ИСКЛЮЧИТЬ ДЛЯ ТЕКУЩЕГО СЛОТА** | SKU XHE с заводским радиатором, отличается от X0E | Габариты несовместимы/не подтверждены для тонкого M.2 в Legion, не рисковать без замеров |

**Выбор под задачу:** конкретный WD SN850X 1TB **без радиатора** у 28BIT за 19 990 ₽ предпочтителен, если доставка в Кострому ≤5 010 ₽ и магазин подтверждает нормальную гарантию/возврат. ADATA Legend 960 без высокого радиатора в XCOM за 18 466 ₽ — разумная альтернатива, 1 524 ₽ экономии; оба в допуске к бюджету до 25 000 ₽ только при подтверждённой доставке. Это товарные карточки «в наличии» при чтении сайта, не резервирование товара и не завершённая оплата. Ссылки на старые карточки, где товар закончился, не объявлять актуальными.

## Базовый эксперимент после покупки

1. Не изменять текущий системный 1TB YMTC; новый SSD — только для моделей.
2. SMART, температура на read-heavy, доступная дисковая ёмкость, включение PCIe4 x4.
3. Нативная Windows сборка Colibrì, pinned checkpoint/quant. Определить 19MB random-read iobench **cold vs buffered**; (важно: thermal throttling после 15+ минут). `iobench` не является тестом token decode.
4. 1–2 реальные APA read-only задачи, измерить TTFT, decode tok/s, peak RAM/VRAM, CPU, disk utilisation, количество ошибок кода по проверенным эталонам.
5. Если скорость ниже желаемой, оставить 744B экспериментальной offline-моделью; для быстрых сотен параллельных тестов использовать более компактную MoE/агентов. Установка модели или запуск code-writing в реальный PLN — только через действующий safe SceneWriter и нативный read-back.

**Итого:** SSD даёт возможность запускать 744B, но сам по себе не гарантирует приемлемую скорость. Исследование не равно закупке, установке или LIVE_PASS.
