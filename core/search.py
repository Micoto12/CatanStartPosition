import logging
from core.vertex import evaluate_vertex_by_top_id, get_available_vertices
from config import ALL_RESOURCES
from collections import Counter
from utils.resource_analysis import calculate_resource_rarity

def find_best_single_placement(structure, hex_id_to_data, occupied_vertices, is_city=False):
    _, scarcity_weight = calculate_resource_rarity(structure, hex_id_to_data)

    available = get_available_vertices(structure, occupied_vertices)
    best_score = -1
    best_vertex = None

    logging.debug(f"Доступно вершин: {len(available)}")
    for top_id in available:
        score = evaluate_vertex_by_top_id(top_id, structure, hex_id_to_data, is_city=is_city, scarcity_weight=scarcity_weight)
        logging.debug(f"  Вершина {top_id}: оценка = {score['total']:.1f}")
        if score["total"] > best_score:
            best_score = score["total"]
            best_vertex = score
            logging.debug(f"    → новый лидер!")

    return best_vertex

def find_best_city_given_my_settlement(structure, hex_id_to_data, occupied_vertices, my_settlement_top_id):
    # Все занятые вершины: чужие + моё поселение
    all_occupied = occupied_vertices | {my_settlement_top_id}
    available = get_available_vertices(structure, all_occupied)

    # Оцениваем наше поселение
    settlement = evaluate_vertex_by_top_id(my_settlement_top_id, structure, hex_id_to_data, is_city=False)

    best_score = -10**9
    best_city = None

    logging.debug(f"Доступно вершин: {len(available)}")
    for top_id in available:
        city = evaluate_vertex_by_top_id(top_id, structure, hex_id_to_data, is_city=True)

        # Объединяем данные
        all_numbers = settlement["numbers"] + city["numbers"]
        all_resources = set(settlement["resources"]) | set(city["resources"])

        # Штраф за дубли чисел
        num_counter = Counter(all_numbers)
        duplication_penalty = sum(count - 1 for count in num_counter.values() if count > 1)
        pair_diversity_bonus = -0.5 * duplication_penalty

        # Штраф за отсутствие ресурсов
        missing_count = len(ALL_RESOURCES - all_resources)
        resource_completeness_bonus = -2.0 * missing_count

        base_total = settlement["total"] + city["total"]
        final_total = base_total + pair_diversity_bonus + resource_completeness_bonus

        logging.debug(f"  Вершина {top_id}: оценка = {final_total:.1f}")
        if final_total > best_score:
            best_score = final_total
            best_city = {
                "city": city,
                "settlement": settlement,
                "total": final_total,
                "base_total": base_total,
                "duplication_penalty": duplication_penalty,
                "missing_resources": list(ALL_RESOURCES - all_resources)
            }
            logging.debug(f"    → новый лидер!")

    return best_city

def find_best_start(structure, hex_id_to_data, occupied_vertices=None):
    if occupied_vertices is None:
        occupied_vertices = set()
    
    best_score = -1
    best_pair = None
    _, scarcity_weight = calculate_resource_rarity(structure, hex_id_to_data)

    # Получаем доступные вершины с учётом занятых
    available_vertices = get_available_vertices(structure, occupied_vertices)
    available_set = set(available_vertices)

    city_scores = {}
    settlement_scores = {}

    for top_id in available_vertices:
        city_scores[top_id] = evaluate_vertex_by_top_id(top_id, structure, hex_id_to_data, is_city=True, scarcity_weight=scarcity_weight)
        settlement_scores[top_id] = evaluate_vertex_by_top_id(top_id, structure, hex_id_to_data, is_city=False, scarcity_weight=scarcity_weight)

    logging.debug(f"Доступно вершин: {len(available_vertices)}")
    for city_id, city in city_scores.items():
        for settle_id, settle in settlement_scores.items():
            if city_id == settle_id:
                continue
            if set(city["hex_ids"]) & set(settle["hex_ids"]):
                continue

            # === 1. Штраф за дублирование чисел в паре ===
            all_numbers = city["numbers"] + settle["numbers"]
            num_counter = Counter(all_numbers)
            duplication_penalty = sum(count - 1 for count in num_counter.values() if count > 1)
            pair_diversity_bonus = -0.5 * duplication_penalty

            # === 2. Штраф за отсутствие ресурсов ===
            all_resources = set(city["resources"]) | set(settle["resources"])
            missing_count = len(ALL_RESOURCES - all_resources)
            resource_completeness_bonus = -2.0 * missing_count

            base_total = city["total"] + settle["total"]
            final_total = base_total + pair_diversity_bonus + resource_completeness_bonus

            logging.debug(f"  Вершина {top_id}: оценка = {final_total:.1f}")
            if final_total > best_score:
                best_score = final_total
                best_pair = {
                    "city": city,
                    "settlement": settle,
                    "total": final_total,
                    "base_total": base_total,
                    "duplication_penalty": duplication_penalty,
                    "missing_resources": list(ALL_RESOURCES - all_resources)
                }
                logging.debug(f"    → новый лидер!")

    return best_pair