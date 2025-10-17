def build_hex_id_to_data(map_data, structure):
    hex_id_to_data = {}
    coord_to_id = {}
    for coord_str, info in structure["coordinates"].items():
        coord_to_id[coord_str] = info["ID"]
    
    for (q, r), data in map_data.items():
        coord_str = f"{q},{r}"
        if coord_str in coord_to_id:
            hex_id = coord_to_id[coord_str]
            hex_id_to_data[hex_id] = data
        else:
            print(f"⚠️ Координата {coord_str} не найдена в структуре!")
    
    return hex_id_to_data