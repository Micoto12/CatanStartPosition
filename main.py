from data_io import load_map_from_json, load_structure
from utils import build_hex_id_to_data, calculate_resource_rarity
from config import DEBUG
from core import find_best_single_placement, find_best_start, find_best_city_given_my_settlement

def main():
    map_data = load_map_from_json("map_data.json")
    structure = load_structure("structure.json")
    hex_id_to_data = build_hex_id_to_data(map_data, structure)

    occupied_vertices = set()

    while True:
        print("\n" + "="*40)
        print("Меню Catan-калькулятора")
        print("="*40)
        print("0. [Отладка] Включить подробные логи")
        print("1. Указать занятые позиции (чужие)")
        print("2. Посчитать расстановку")
        print("3. Выход")
        choice = input("\nВыберите пункт: ").strip()

        if choice == "1":
            print("\nТекущие занятые вершины:", sorted(occupied_vertices) if occupied_vertices else "нет")
            user_input = input("Введите занятые вершины (через запятую, например: 12,45,67) или оставьте пустым для сброса: ").strip()
            if user_input == "":
                occupied_vertices = set()
                print("✅ Занятые вершины сброшены.")
            else:
                try:
                    new_occupied = {int(x.strip()) for x in user_input.split(",")}
                    occupied_vertices = new_occupied
                    print(f"✅ Занято вершин: {len(occupied_vertices)}")
                except ValueError:
                    print("❌ Ошибка: введите числа через запятую.")

        elif choice == "2":
            print("\n2.1 Посчитать поселение")
            print("2.2 Посчитать город (независимо)")
            print("2.3 Посчитать пару (город + поселение)")
            print("2.4 Город с учётом моего поселения")
            sub_choice = input("Выберите (1–4): ").strip()

            if sub_choice == "1":
                best = find_best_single_placement(structure, hex_id_to_data, occupied_vertices, is_city=False)
                obj = "поселение"
            elif sub_choice == "2":
                best = find_best_single_placement(structure, hex_id_to_data, occupied_vertices, is_city=True)
                obj = "город"
            elif sub_choice == "3":
                best_pair = find_best_start(structure, hex_id_to_data, occupied_vertices)
                if best_pair:
                    print("\n✅ Лучшая пара:")
                    print(f"Город: {best_pair['city']['top_id']} | {best_pair['city']['resources']} | {best_pair['city']['numbers']}")
                    print(f"Поселение: {best_pair['settlement']['top_id']} | {best_pair['settlement']['resources']} | {best_pair['settlement']['numbers']}")
                    missing = best_pair.get("missing_resources", [])
                    if missing:
                        print(f"⚠️ Отсутствуют ресурсы: {missing}")
                    else:
                        print("✅ Все 5 ресурсов!")
                    print(f"Итог: {best_pair['total']:.1f}")
                else:
                    print("❌ Нет допустимых пар.")
                continue
            elif sub_choice == "4":
                if not occupied_vertices:
                    print("⚠️ Сначала укажите чужие занятые вершины (пункт 1).")
                    continue
                try:
                    my_settlement_id = int(input("Введите ID вашей вершины с поселением: ").strip())
                except ValueError:
                    print("❌ Неверный ID.")
                    continue
                if my_settlement_id in occupied_vertices:
                    print("⚠️ Ваше поселение не должно быть в списке чужих занятых вершин.")
                    continue
                best = find_best_city_given_my_settlement(
                    structure, hex_id_to_data, occupied_vertices, my_settlement_id
                )
                if best:
                    print("\n✅ Лучшее место для города с учётом вашего поселения:")
                    print(f"Ваше поселение: {best['settlement']['top_id']} | {best['settlement']['resources']} | {best['settlement']['numbers']}")
                    print(f"Город: {best['city']['top_id']} | {best['city']['resources']} | {best['city']['numbers']}")
                    missing = best.get("missing_resources", [])
                    if missing:
                        print(f"⚠️ Отсутствуют ресурсы: {missing}")
                    else:
                        print("✅ Все 5 ресурсов!")
                    print(f"Итоговая оценка: {best['total']:.1f}")
                    resource_total, _ = calculate_resource_rarity(structure, hex_id_to_data)
                    print("\n📊 Дефицит ресурсов (чем меньше — тем ценнее):")
                    for res, total in sorted(resource_total.items(), key=lambda x: x[1]):
                        print(f"  {res}: {total}")
                else:
                    print("❌ Нет доступных мест для города.")
                continue
            else:
                print("❌ Неверный выбор.")
                continue

            if best:
                print(f"\n✅ Лучшее место для {obj}:")
                print(f"Вершина {best['top_id']}")
                print(f"Ресурсы: {best['resources']}")
                print(f"Числа: {best['numbers']}")
                resource_total, _ = calculate_resource_rarity(structure, hex_id_to_data)
                print("\n📊 Дефицит ресурсов (чем меньше — тем ценнее):")
                for res, total in sorted(resource_total.items(), key=lambda x: x[1]):
                    print(f"  {res}: {total}")
                print(f"Оценка: {best['total']:.1f}")
            else:
                print(f"❌ Нет доступных мест для {obj}а.")
        elif choice == "0":
            import config
            config.DEBUG = not config.DEBUG
            print(f"📝 Логирование {'включено' if config.DEBUG else 'выключено'}")
            # Перезапустить логгер
            if config.DEBUG:
                import logging
                logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
            else:
                import logging
                logging.disable(logging.CRITICAL)
            continue
        elif choice == "3":
            print("До встречи в Катане! 🏝️")
            break

        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()