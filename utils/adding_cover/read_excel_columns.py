import pandas as pd


def read_excel_columns_to_map(file_path, header_row, col1_name, col2_name):
    try:
        df = pd.read_excel(file_path, header=None)

        header = df.iloc[header_row - 1]

        col1_index = None
        col2_index = None
        for idx, value in enumerate(header):
            if isinstance(value, str) and col1_name in value:
                col1_index = idx
            if isinstance(value, str) and col2_name in value:
                col2_index = idx

        if col1_index is None or col2_index is None:
            raise ValueError(
                f"Не удалось найти столбцы '{col1_name}' или '{col2_name}' в строке {header_row}. Содержимое строки заголовков: {header.tolist()}")

        data_df = df.iloc[header_row:].copy()

        data_df.columns = [f"col_{i}" for i in range(len(data_df.columns))]
        result = data_df[[data_df.columns[col1_index], data_df.columns[col2_index]]].dropna().reset_index(drop=True)
        result.columns = [col1_name, col2_name]

        result_map = {}
        for _, row in result.iterrows():
            first_word = str(row[col1_name]).split()[0] if isinstance(row[col1_name], str) and row[
                col1_name].strip() else None
            if first_word:
                result_map[first_word] = row[col2_name]

        return result_map

    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден")
        return None
    except ValueError as e:
        print(f"Ошибка: {e}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def get_surnames_and_covers_from_table(file_path, header_row, col1_name, col2_name):
    data = read_excel_columns_to_map(file_path, header_row, col1_name, col2_name)

    if data:
        for key, value in data.items():
            print(f"{key}: {value}")

    return data


if __name__ == "__main__":
    file_path = r"C:\programms\undr\класс.xlsx"

    header_row = 1

    col1_name = "Фамилия Имя"
    col2_name = "Номер обложки"

    get_surnames_and_covers_from_table(file_path, header_row,
                                       col1_name, col2_name)
