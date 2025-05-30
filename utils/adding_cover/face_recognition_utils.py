import face_recognition


def get_face_encodings(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    encodings = face_recognition.face_encodings(image, face_locations)

    return image, face_locations, encodings


def get_top_faces(locations, encodings, top_n=2):
    # locations: список кортежей (top, right, bottom, left)
    # encodings: список эмбеддингов в том же порядке

    # Получаем индексы сортировки по координате top (от меньшего к большему)
    sorted_indices = sorted(range(len(locations)), key=lambda i: locations[i][0])
    # Берём индексы верхних top_n лиц
    selected_indices = sorted_indices[:top_n]
    # Возвращаем только выбранные лица и их эмбеддинги
    locations = [locations[i] for i in selected_indices]
    encodings = [encodings[i] for i in selected_indices]

    return locations, encodings


def preprocess_collages(collage_paths):
    collages_data = []
    for path in collage_paths:
        image, locations, encodings = get_face_encodings(path)
        locations, encodings = get_top_faces(locations, encodings, top_n=2) if len(locations) > 4 else (
            locations, encodings)
        collages_data.append({
            "path": path,
            "image": image,
            "locations": locations,
            "encodings": encodings
        })
    return collages_data
