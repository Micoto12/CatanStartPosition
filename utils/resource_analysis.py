from config import PROB

def calculate_resource_rarity(structure, hex_id_to_data):
    resource_total = {
        "forest": 0,
        "pasture": 0,
        "fields": 0,
        "mountains": 0,
        "hills": 0
    }

    has_extreme = {res: False for res in resource_total}

    for hex_id, data in hex_id_to_data.items():
        res = data["resource"]
        num = data["number"]
        if res in resource_total and num != 7:
            resource_total[res] += PROB.get(num, 0)
            if num in (2, 12):
                resource_total[res] -= 1

    # Нормализуем: чем меньше total — тем выше дефицит → выше вес
    max_prob = max(resource_total.values())
    scarcity_weight = {}
    for res, total in resource_total.items():
        if max_prob > 0:
            scarcity_weight[res] = 1.0 + (max_prob - total) / max_prob
        else:
            scarcity_weight[res] = 1.0

    return resource_total, scarcity_weight