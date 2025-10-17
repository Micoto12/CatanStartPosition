from config import PROB

def calculate_resource_rarity(structure, hex_id_to_data):
    """
    Возвращает словарь: resource -> total_probability
    и нормализованный "вес дефицитности" (чем ниже шанс — выше вес).
    """
    resource_total = {
        "forest": 0,
        "pasture": 0,
        "fields": 0,
        "mountains": 0,
        "hills": 0
    }

    for hex_id, data in hex_id_to_data.items():
        res = data["resource"]
        num = data["number"]
        if res in resource_total and num != 7:
            resource_total[res] += PROB.get(num, 0)

    # Нормализуем: чем меньше total — тем выше дефицит → выше вес
    max_prob = max(resource_total.values())
    scarcity_weight = {}
    for res, total in resource_total.items():
        if max_prob > 0:
            # Пример: если total = 10, max = 20 → вес = 1.0
            # если total = 5 → вес = 1.5
            scarcity_weight[res] = 1.0 + (max_prob - total) / max_prob
        else:
            scarcity_weight[res] = 1.0

    return resource_total, scarcity_weight