#!/usr/bin/env python3
"""
Тестовый запуск обновленной функциональности main.py
"""

import sys
import os
import re

# Добавляем директорию src в путь поиска модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from drawio_processor import DrawIOProcessor


def main():
    """
    Тестовая главная функция
    """
    # Используем каталог data в текущей директории проекта
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Проверяем существование каталога
    if not os.path.isdir(data_dir):
        print(f"Каталог {data_dir} не существует.")
        return

    # Создаем экземпляр процессора drawio
    processor = DrawIOProcessor(data_dir)

    # Получаем список файлов
    files = processor.get_drawio_files()
    if not files:
        print("В каталоге нет файлов с расширением .drawio")
        return

    # Автоматически выбираем первый файл для тестирования
    selected_file = files[0]
    print(f"Выбран файл: {selected_file}")

    print(f"\nИзвлечение stencils <имя из шаблона stencil_templates>...")

    # Загружаем шаблоны
    templates = processor.load_stencil_templates()
    if not templates:
        print("Не удалось загрузить шаблоны.")
        return

    # Словарь для хранения результатов по каждому шаблону
    results_by_template = {}

    # Перебираем все шаблоны из файла и последовательно ищем их в исходном файле
    for template_name, template_config in templates.items():
        print(f"Поиск шаблона: {template_name}")

        # Ищем объекты для текущего шаблона
        matched_objects = []

        # Читаем файл
        root = processor.parse_drawio_structure(selected_file)
        if root is None:
            print(f"Не удалось разобрать файл {selected_file}")
            continue

        # Ищем все элементы mxCell с атрибутом style, содержащим информацию о stencil
        for element in root.iter():
            if element.tag == 'mxCell':
                style = element.get('style', '')
                value = element.get('value', '')

                # Проверяем, содержит ли стиль информацию о stencil
                if 'shape=stencil(' in style.lower():
                    matched = False

                    # Проверяем паттерны в значении элемента
                    if 'patterns' in template_config:
                        for pattern in template_config['patterns']:
                            # Для нового формата объединяем все критерии в один паттерн
                            if pattern.lower() in (style + ' ' + value).lower():
                                matched = True
                                break

                    # Если не нашли совпадение в значении, проверяем стиль
                    if not matched and 'patterns' in template_config:
                        cell_style = style.lower()
                        for pattern in template_config['patterns']:
                            if pattern.lower() in cell_style:
                                matched = True
                                break

                    if matched:
                        # Извлекаем дополнительные данные с помощью парсеров
                        extracted_data = {}
                        ip_addresses = []  # Список найденных IP-адресов для последующего удаления из описания

                        if 'parsers' in template_config:
                            for parser_item in template_config['parsers']:
                                for data_name, regex_pattern in parser_item.items():
                                    matches = re.findall(regex_pattern, value, re.IGNORECASE)
                                    if matches:
                                        extracted_data[data_name] = matches

                                        # Сохраняем найденные IP-адреса для последующего использования
                                        if data_name == 'ip':
                                            ip_addresses.extend(matches)

                        # Для типа Network извлекаем описание как остаток текста без IP-адресов
                        if template_name == 'Network':
                            desc_text = value
                            # Удаляем все найденные IP-адреса из текста
                            for ip_addr in ip_addresses:
                                desc_text = re.sub(re.escape(ip_addr), '', desc_text)
                            # Очищаем текст описания от HTML тегов и лишних пробелов
                            desc_text = re.sub('<[^<]+?>', '', desc_text).strip()
                            # Убираем лишние пробелы и переносы строк
                            desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                            # Убираем специальные символы, оставшиеся после очистки HTML
                            desc_text = desc_text.replace('&nbsp;', ' ').strip()
                            desc_text = re.sub(r'\s+', ' ', desc_text).strip()  # Еще раз нормализуем пробелы
                            # Проверяем, что текст содержит осмысленную информацию (не только HTML-остатки)
                            # Убираем все не-буквенные и не-цифровые символы, кроме пробелов
                            meaningful_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s]', ' ', desc_text).strip()
                            meaningful_text = re.sub(r'\s+', ' ', meaningful_text).strip()  # Нормализуем пробелы
                            # Проверяем, есть ли в тексте хотя бы одна буква или цифра
                            has_meaningful_chars = bool(re.search(r'[a-zA-Zа-яА-ЯёЁ0-9]', meaningful_text))
                            if meaningful_text and has_meaningful_chars:  # Добавляем только если текст содержит осмысленные символы
                                extracted_data['description'] = [desc_text]

                        # Извлекаем информацию о найденном объекте
                        obj_info = {
                            'id': element.get('id', ''),
                            'value': element.get('value', ''),
                            'style': style,
                            'parent': element.get('parent', ''),
                            'vertex': element.get('vertex', ''),
                            'geometry': element.find('mxGeometry'),
                            'matched_type': template_name,
                            'schema': template_config.get('schema', 'none'),
                            'extracted_data': extracted_data
                        }
                        matched_objects.append(obj_info)

        # Сохраняем результаты для текущего шаблона
        results_by_template[template_name] = matched_objects
        print(f"  Найдено объектов: {len(matched_objects)}")

    # Выводим сводный отчет
    print("\n" + "="*60)
    print("СВОДНЫЙ ОТЧЕТ ПО НАЙДЕННЫМ STENCILS")
    print("="*60)

    total_objects = 0
    for template_name, objects in results_by_template.items():
        if objects:
            print(f"\nШаблон: {template_name}")
            for obj in objects:
                print(f"  - ID: {obj['id']}")
                print(f"    Значение: {obj['value'][:100]}{'...' if len(obj['value']) > 100 else ''}")
                if obj['extracted_data']:
                    print(f"    Данные: {obj['extracted_data']}")
            print(f"  Обнаружено объектов: {len(objects)}")
            total_objects += len(objects)
        else:
            print(f"\nШаблон: {template_name}")
            print(f"  Обнаружено объектов: 0")

    print("\n" + "="*60)
    print(f"ИТОГО: Обнаружено объектов {total_objects}")
    print("="*60)


if __name__ == "__main__":
    main()