#!/usr/bin/env python3
"""
Главный файл для запуска обработки файлов drawio
"""

import sys
import os

# Добавляем директорию src в путь поиска модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


GREEN = "\033[32m"
RESET = "\033[0m"


from drawio_processor import DrawIOProcessor


def main():
    """
    Главная функция
    """
    # Проверяем, передан ли путь к каталогу как аргумент командной строки
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        # По умолчанию используем каталог data в текущей директории проекта
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Проверяем существование каталога
    if not os.path.isdir(data_dir):
        print(f"Каталог {data_dir} не существует.")
        return

    # Создаем экземпляр процессора drawio
    processor = DrawIOProcessor(data_dir)

    # Показываем меню и ждем выбора файла
    selected_file = processor.show_menu_and_select_file()

    if selected_file:
        # Используем новый метод из библиотеки для поиска всех стencилов по шаблонам
        results_by_template = processor.find_stencils_by_all_templates(selected_file)

        # Выводим информацию о поиске шаблонов и количестве найденных объектов
        for template_name, matched_objects in results_by_template.items():
            # Выводим сообщение об этапе работы с подстановкой имени шаблона
            print(f"\nИзвлечение stencils {GREEN}{template_name}{RESET}", end="")
            print(f"  Найдено объектов: {len(matched_objects)}")

        # Используем метод из библиотеки для генерации сводного отчета
        processor.generate_summary_report(results_by_template)


if __name__ == "__main__":
    main()