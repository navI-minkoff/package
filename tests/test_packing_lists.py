from utils.photoshop_utils import packingLists, packagingSpreads, packagingGroup, packingLastListsWithGroupPages
from utils.file_utils import getJpegFilenames
from utils.tests_utils import parse_standard, parse_spreads, parse_with_individual_lists, parse_with_individual_lists_and_groups, parse_with_individual_groups


def run_case_spreads(ps, doc, jpeg_options, parsed, output_dir, album_type):
    packagingSpreads(
        ps, doc, jpeg_options,
        parsed["folder_path"], parsed["jpeg_filenames"], parsed["teacher_path"],
        output_dir, album_type
    )

def run_case_lists(ps, doc, jpeg_options, parsed, output_dir, album_type):
    packingLists(
        ps, doc, jpeg_options,
        parsed["folder_path"], parsed["jpeg_filenames"],
        output_dir, 1, album_type
    )

def run_case_lists_groups(ps, doc, jpeg_options, parsed, output_dir, album_type):
    packingLastListsWithGroupPages(
        ps, doc, jpeg_options,
        parsed.get("lists_jpeg", []), parsed.get("groups_jpeg", []),
        output_dir, album_type
    )

def run_case_groups(ps, doc, jpeg_options, parsed, output_dir, album_type):
    packagingGroup(
        ps, doc, jpeg_options,
        parsed["folder_path"], parsed["jpeg_filenames"],
        output_dir, "01", "000", album_type, True
    )

def dispatch_case(test_case, input_dir):
    if "spreads" in test_case:
        return parse_spreads(input_dir), run_case_spreads
    elif "with_individual_lists_and_groups" in test_case:
        return parse_with_individual_lists_and_groups(input_dir), run_case_lists_groups
    elif "with_individual_lists" in test_case and "lists_groups" in test_case:
        # Индивидуальные списки для lists_groups
        parsed = parse_with_individual_lists(input_dir)
        parsed.update(parse_with_individual_groups(input_dir))
        return parsed, run_case_lists_groups
    elif "with_individual_groups" in test_case and "lists_groups" in test_case:
        parsed = parse_with_individual_groups(input_dir)
        parsed.update(parse_with_individual_lists(input_dir))
        return parsed, run_case_lists_groups
    elif "lists_groups" in test_case:
        # Стандартные lists_groups
        parsed = parse_standard(input_dir)
        return {"lists_jpeg": [{
                    "lists_folder_path": parsed["folder_path"],
                    "lists_jpeg_filenames": parsed["jpeg_filenames"],
                    "postfix": "000"
                }],
                "groups_jpeg": [{
                    "groups_jpeg": parsed["folder_path"],
                    "group_jpeg_filenames": parsed["jpeg_filenames"],
                    "postfix": "000"
                }]
                }, run_case_lists_groups
    elif "with_individual_lists" in test_case:
        return parse_with_individual_lists(input_dir), run_case_lists_groups
    elif "with_individual_groups" in test_case:
        return parse_with_individual_groups(input_dir), run_case_lists_groups
    elif "lists" in test_case:
        return parse_standard(input_dir), run_case_lists
    elif "groups" in test_case:
        return parse_standard(input_dir), run_case_groups
    else:
        raise ValueError(f"Неизвестный тип теста: {test_case}")



