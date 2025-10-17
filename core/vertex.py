import logging
from config import PROB, COMMODITY_RESOURCES, DEBUG
from collections import Counter

if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
else:
    logging.disable(logging.CRITICAL)

def evaluate_vertex_by_top_id(target_top_id, structure, hex_id_to_data, is_city=False, scarcity_weight=None):

    top = None
    for v in structure["tops"].values():
        if v["top_ID"] == target_top_id:
            top = v
            break
    if top is None:
        raise ValueError(f"Вершина с top_ID={target_top_id} не найдена!")

    ids = [top["ID1"], top["ID2"], top["ID3"]]
    numbers = []
    total_score = 0
    resources = set()
    commodity_score = 0

    for hid in ids:
        if hid == 0 or hid not in hex_id_to_data:
            continue
        h = hex_id_to_data[hid]
        num = h["number"]
        res = h["resource"]
        if num == 7:
            continue
        numbers.append(num)
        p = PROB.get(num, 0)
        mult = 2 if is_city else 1
        total_score += p * mult
        resources.add(res)
        if is_city and res in COMMODITY_RESOURCES:
            commodity_score += p
    
    num_counter = Counter(numbers)
    duplication_penalty = sum(count - 1 for count in num_counter.values() if count > 1)
    number_diversity_bonus = -0.5 * duplication_penalty

    scarcity_bonus = 0
    if scarcity_weight:
        for res in resources:
            if res in scarcity_weight:
                # Бонус пропорционален весу дефицита
                scarcity_bonus += scarcity_weight[res] * 0.3  # настраиваемый множитель

    diversity = len(resources)
    total = (
        total_score 
        + 0.5 * commodity_score 
        + diversity 
        + number_diversity_bonus
        + scarcity_bonus
    )

    logging.debug(f"Оценка вершины {target_top_id} (город={is_city}):")
    logging.debug(f"  Гексы: {ids}")
    logging.debug(f"  Числа: {numbers}")
    logging.debug(f"  Ресурсы: {list(resources)}")
    logging.debug(f"  Базовый скор: {total_score}")
    logging.debug(f"  Товары: {commodity_score}")
    logging.debug(f"  Штраф за дубли чисел: {number_diversity_bonus}")
    logging.debug(f"  Бонус дефицитного ресурса {scarcity_bonus}")
    logging.debug(f"  Итого: {total}")

    return {
        "top_id": target_top_id,
        "resource_score": total_score,
        "commodity_score": commodity_score,
        "number_diversity_bonus": number_diversity_bonus,
        "scarcity_bonus": scarcity_bonus,
        "diversity": diversity,
        "total": total,
        "resources": list(resources),
        "numbers": numbers,
        "hex_ids": [hid for hid in ids if hid != 0]
    }

def get_available_vertices(structure, occupied_vertices):
    """
    Возвращает список top_ID, доступных для постройки,
    с учётом правила: нельзя строить на соседних вершинах (делящих 2 гекса).
    """
    # Собираем все вершины в виде: top_ID -> set(hex_ids)
    all_vertices = {}
    for v in structure["tops"].values():
        top_id = v["top_ID"]
        hexes = {v["ID1"], v["ID2"], v["ID3"]} - {0}
        all_vertices[top_id] = hexes

    # Множество запрещённых вершин
    forbidden = set(occupied_vertices)  # сами занятые — запрещены

    # Для каждой занятой вершины находим её соседей (делящих 2 гекса)
    for occ_id in occupied_vertices:
        if occ_id not in all_vertices:
            continue
        occ_hexes = all_vertices[occ_id]
        # Все пары гексов из занятой вершины
        hex_list = list(occ_hexes)
        pairs = []
        for i in range(len(hex_list)):
            for j in range(i + 1, len(hex_list)):
                pairs.append({hex_list[i], hex_list[j]})

        # Ищем вершины, содержащие любую из этих пар
        for top_id, hexes in all_vertices.items():
            if top_id == occ_id:
                continue
            for pair in pairs:
                if pair.issubset(hexes):
                    forbidden.add(top_id)
                    break  # одна пара — достаточно

    # Доступные = все вершины минус запрещённые
    available = [top_id for top_id in all_vertices.keys() if top_id not in forbidden]
    return available