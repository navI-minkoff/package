def generateStrings(prefix, start, end):
    result = []
    for i in range(start, end + 1):
        formatted_number = f"{prefix}-{i:03}"
        result.append(formatted_number)
    return result


def generatePrefixes(start, prefix_count, postfix='000'):
    postfix.zfill(3)
    prefixes = []
    for i in range(start, start + prefix_count):
        formatted_prefix = f"{i:02}-{postfix}"
        prefixes.append(formatted_prefix)
    return prefixes
