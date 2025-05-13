import os
from utils.file_utils import getJpegFilenames, extractNumber


import os
from utils.file_utils import getJpegFilenames


def parse_standard(input_dir):
    from utils.file_utils import getJpegFilenames
    files = getJpegFilenames(input_dir)
    return {
        "folder_path": input_dir,
        "jpeg_filenames": files
    }
def parse_spreads(input_dir):
    student_dir = os.path.join(input_dir, "student")
    teacher_dir = os.path.join(input_dir, "teacher")
    student_files = sorted(getJpegFilenames(student_dir), key=extractNumber)
    teacher_files = sorted(getJpegFilenames(teacher_dir), key=extractNumber)
    if not teacher_files:
        raise ValueError("В папке teacher нет фотографий!")
    teacher_path = os.path.join(teacher_dir, teacher_files[0])
    return {
        "folder_path": student_dir,
        "jpeg_filenames": student_files,
        "teacher_path": teacher_path
    }

def parse_with_individual_lists(input_dir):
    from utils.file_utils import getJpegFilenames
    import os
    lists_jpeg = []
    general_dir = os.path.join(input_dir, "general")
    individual_dir = os.path.join(input_dir, "individual")
    if os.path.isdir(general_dir):
        files = sorted(getJpegFilenames(general_dir), key=extractNumber),
        if files:
            lists_jpeg.append({
                "lists_folder_path": general_dir,
                "lists_jpeg_filenames": files,
                "postfix": "000"
            })
    if os.path.isdir(individual_dir):
        files = sorted(getJpegFilenames(individual_dir), key=extractNumber)
        for fname in files:
            lists_jpeg.append({
                "lists_folder_path": individual_dir,
                "lists_jpeg_filenames": [fname],
                "postfix": fname.split(' ')[0].zfill(3)
            })
    return {"lists_jpeg": lists_jpeg}

def parse_groups(input_dir):
    """
    Универсальный парсер групп:
    - Если в input_dir лежат просто файлы - возвращает один элемент с postfix "000"
    - Если есть папки general и individual - парсит их как индивидуальные группы
    """
    groups_jpeg = []

    # Проверяем, есть ли папки general и individual
    general_dir = os.path.join(input_dir, "general")
    individual_dir = os.path.join(input_dir, "individual")

    if os.path.isdir(general_dir) or os.path.isdir(individual_dir):
        # Парсим general
        if os.path.isdir(general_dir):
            files = getJpegFilenames(general_dir)
            if files:
                groups_jpeg.append({
                    "groups_jpeg": general_dir,
                    "group_jpeg_filenames": files,
                    "postfix": "000"
                })
        # Парсим individual
        if os.path.isdir(individual_dir):
            for folder_name in sorted(os.listdir(individual_dir)):
                folder_path = os.path.join(individual_dir, folder_name)
                if os.path.isdir(folder_path):
                    files = getJpegFilenames(folder_path)
                    if files:
                        postfix = folder_name.split(' ')[0].zfill(3)
                        groups_jpeg.append({
                            "groups_jpeg": folder_path,
                            "group_jpeg_filenames": files,
                            "postfix": postfix
                        })
    else:
        # Просто файлы в input_dir - обычные групповые
        files = getJpegFilenames(input_dir)
        if files:
            groups_jpeg.append({
                "groups_jpeg": input_dir,
                "group_jpeg_filenames": files,
                "postfix": "000"
            })

    return {"groups_jpeg": groups_jpeg}

def parse_with_individual_lists_and_groups(input_dir):
    from utils.file_utils import getJpegFilenames
    import os
    lists_jpeg = []
    groups_jpeg = []
    list_dir = os.path.join(input_dir, "list")
    group_dir = os.path.join(input_dir, "group")
    # lists
    for sub in ["general", "individual"]:
        sub_dir = os.path.join(list_dir, sub)
        if os.path.isdir(sub_dir):
            files = getJpegFilenames(sub_dir)
            for fname in files:
                lists_jpeg.append({
                    "lists_folder_path": sub_dir,
                    "lists_jpeg_filenames": [fname],
                    "postfix": fname.split(' ')[0].zfill(3)
                })
    # groups
    for sub in ["general", "individual"]:
        sub_dir = os.path.join(group_dir, sub)
        if os.path.isdir(sub_dir):
            if sub == "individual":
                for folder in sorted(os.listdir(sub_dir)):
                    path = os.path.join(sub_dir, folder)
                    if os.path.isdir(path):
                        files = sorted(getJpegFilenames(path), key=extractNumber)
                        if files:
                            groups_jpeg.append({
                                "groups_jpeg": path,
                                "group_jpeg_filenames": files,
                                "postfix": folder.split(' ')[0].zfill(3)
                            })
            else:
                files = sorted(getJpegFilenames(sub_dir), key=extractNumber)
                for fname in files:
                    groups_jpeg.append({
                        "groups_jpeg": sub_dir,
                        "group_jpeg_filenames": [fname],
                        "postfix": fname.split(' ')[0].zfill(3)
                    })
    return {"lists_jpeg": lists_jpeg, "groups_jpeg": groups_jpeg}

