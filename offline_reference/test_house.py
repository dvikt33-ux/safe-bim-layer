raise SystemExit('offline reference is not a runtime entry and performs no Tapir call')
from pathlib import Path
import json
import sys

from safe_bim_layer import TapirClient, SafeBIMLayer, SafeBIMError


# ============================================================
# НАСТРОЙКИ
# ============================================================

BRIDGE = "http://127.0.0.1:19723"

# Файл Archicad, в котором разрешено строить тестовый дом
PROJECT = r"C:\Users\Admin\Downloads\Test_House.pln"

# Схема Tapir должна лежать рядом с этим Python-файлом
SCHEMA = str(Path(__file__).parent / "tapir-1.5.8.json")


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ПРОВЕРКА
# ============================================================

def require_pass(name, result):
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    status = result.get("status")
    print("STATUS:", status)
    print("GUIDS:", result.get("guids", []))

    if status != "PASS":
        print()
        print("DIFF:")
        print(
            json.dumps(
                result.get("diff", []),
                ensure_ascii=False,
                indent=2
            )
        )
        raise RuntimeError(f"{name}: FAIL")

    return result


# ============================================================
# ЗАПУСК
# ============================================================

def main():

    print("TEST HOUSE")
    print("Project:", PROJECT)
    print("Bridge:", BRIDGE)
    print()

    # --------------------------------------------------------
    # 1. Проверяем существование PLN
    # --------------------------------------------------------

    project_path = Path(PROJECT)

    if not project_path.exists():
        raise FileNotFoundError(
            f"Файл Archicad не найден:\n{PROJECT}"
        )

    if not Path(SCHEMA).exists():
        raise FileNotFoundError(
            f"Не найден tapir-1.5.8.json:\n{SCHEMA}"
        )

    # --------------------------------------------------------
    # 2. Подключаемся к Tapir
    # --------------------------------------------------------

    client = TapirClient(
        base_url=BRIDGE,
        schema_path=SCHEMA
    )

    bim = SafeBIMLayer(client)

    # --------------------------------------------------------
    # 3. ЯВНО открываем Test_House.pln
    # --------------------------------------------------------

    print("Открываю Test_House.pln...")

    open_result = client.call(
        "OpenProject",
        {
            "projectFilePath": PROJECT
        }
    )

    print(
        json.dumps(
            open_result,
            ensure_ascii=False,
            indent=2
        )
    )

    # --------------------------------------------------------
    # 4. Проверяем, что Archicad отвечает
    # --------------------------------------------------------

    print()
    print("Проверяю открытый проект...")

    project_info = client.call(
        "GetProjectInfo",
        {}
    )

    print(
        json.dumps(
            project_info,
            ensure_ascii=False,
            indent=2
        )
    )

    # ========================================================
    # ГЕОМЕТРИЯ
    # ========================================================

    # Дом 10 × 8 м

    contour = [
        {"x": 0.0, "y": 0.0},
        {"x": 10.0, "y": 0.0},
        {"x": 10.0, "y": 8.0},
        {"x": 0.0, "y": 8.0},
        {"x": 0.0, "y": 0.0},
    ]

    WALL_HEIGHT = 3.0
    WALL_THICKNESS = 0.25
    SLAB_THICKNESS = 0.20

    WINDOW_WIDTH = 1.5
    WINDOW_HEIGHT = 1.4
    WINDOW_SILL = 0.9

    # ========================================================
    # 1 ЭТАЖ
    # ========================================================

    print()
    print("Создаю стены 1 этажа...")

    walls_1 = require_pass(
        "Стены 1 этажа",
        bim.create_wall_loop(
            contour=contour,
            floor_index=0,
            height=WALL_HEIGHT,
            thickness=WALL_THICKNESS,
        )
    )

    wall1 = walls_1["guids"]

    # --------------------------------------------------------
    # ПОЛ / НИЖНЕЕ ПЕРЕКРЫТИЕ
    # --------------------------------------------------------

    require_pass(
        "Перекрытие 1 этажа",
        bim.create_basic_slab(
            contour=contour,
            level=0.0,
            floor_index=0,
            thickness=SLAB_THICKNESS,
        )
    )

    # --------------------------------------------------------
    # ОКНА 1 ЭТАЖА
    # --------------------------------------------------------

    windows_floor_1 = [
        # фасад 10 м
        (wall1[0], 2.5),
        (wall1[0], 7.5),

        # правая стена 8 м
        (wall1[1], 4.0),

        # задняя стена 10 м
        (wall1[2], 2.5),
        (wall1[2], 7.5),

        # левая стена 8 м
        (wall1[3], 4.0),
    ]

    for number, (wall_guid, offset) in enumerate(
        windows_floor_1,
        start=1
    ):
        require_pass(
            f"Окно 1 этажа №{number}",
            bim.insert_window(
                wall_guid,
                {
                    "centerOffset": offset,
                    "sillHeight": WINDOW_SILL,
                    "width": WINDOW_WIDTH,
                    "height": WINDOW_HEIGHT,
                }
            )
        )

    # ========================================================
    # 2 ЭТАЖ
    # ========================================================

    print()
    print("Создаю стены 2 этажа...")

    walls_2 = require_pass(
        "Стены 2 этажа",
        bim.create_wall_loop(
            contour=contour,
            floor_index=1,
            height=WALL_HEIGHT,
            thickness=WALL_THICKNESS,
        )
    )

    wall2 = walls_2["guids"]

    # --------------------------------------------------------
    # МЕЖЭТАЖНОЕ ПЕРЕКРЫТИЕ
    # --------------------------------------------------------

    require_pass(
        "Межэтажное перекрытие",
        bim.create_basic_slab(
            contour=contour,
            level=0.0,
            floor_index=1,
            thickness=SLAB_THICKNESS,
        )
    )

    # --------------------------------------------------------
    # ОКНА 2 ЭТАЖА
    # --------------------------------------------------------

    windows_floor_2 = [
        (wall2[0], 2.5),
        (wall2[0], 7.5),

        (wall2[1], 4.0),

        (wall2[2], 2.5),
        (wall2[2], 7.5),

        (wall2[3], 4.0),
    ]

    for number, (wall_guid, offset) in enumerate(
        windows_floor_2,
        start=1
    ):
        require_pass(
            f"Окно 2 этажа №{number}",
            bim.insert_window(
                wall_guid,
                {
                    "centerOffset": offset,
                    "sillHeight": WINDOW_SILL,
                    "width": WINDOW_WIDTH,
                    "height": WINDOW_HEIGHT,
                }
            )
        )

    # ========================================================
    # КРЫШЕЧНОЕ ПЕРЕКРЫТИЕ
    # ========================================================

    require_pass(
        "Верхнее перекрытие",
        bim.create_basic_slab(
            contour=contour,
            level=3.0,
            floor_index=1,
            thickness=SLAB_THICKNESS,
        )
    )

    # ========================================================
    # ГОТОВО
    # ========================================================

    print()
    print("=" * 60)
    print("TEST HOUSE: PASS")
    print("=" * 60)

    print("Создано:")
    print("  8 наружных стен")
    print("  3 перекрытия")
    print("  12 окон")
    print()
    print("Размер здания: 10 × 8 м")
    print("Этажей: 2")
    print("Высота этажа: 3 м")
    print("Толщина стен: 250 мм")
    print("Толщина перекрытий: 200 мм")
    print()
    print("Файл:")
    print(PROJECT)


# ============================================================
# ОБРАБОТКА ОШИБОК
# ============================================================

if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print()
        print("=" * 60)
        print("TEST HOUSE: ERROR")
        print("=" * 60)
        print(type(error).__name__ + ":")
        print(error)

        sys.exit(1)