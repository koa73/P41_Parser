"""
Модуль для работы с файлами drawio
"""

import os
import xml.etree.ElementTree as ET
from typing import List, Optional
import yaml
import re


class DrawIOProcessor:
    """
    Класс для обработки файлов drawio
    """

    def __init__(self, data_dir: str):
        """
        Инициализация процессора drawio

        :param data_dir: путь к каталогу с файлами drawio
        """
        self.data_dir = data_dir
        self.selected_file = None

    def get_drawio_files(self) -> List[str]:
        """
        Получение списка файлов drawio в каталоге

        :return: список файлов drawio
        """
        drawio_files = []
        for file in os.listdir(self.data_dir):
            if file.lower().endswith('.drawio'):
                drawio_files.append(file)
        return drawio_files

    def show_menu_and_select_file(self) -> Optional[str]:
        """
        Отображение интерактивного меню и выбор файла

        :return: выбранный файл или None, если файл не выбран
        """
        drawio_files = self.get_drawio_files()

        if not drawio_files:
            print("В каталоге нет файлов с расширением .drawio")
            return None

        print("Доступные файлы drawio:")
        for idx, file in enumerate(drawio_files, 1):
            print(f"{idx}. {file}")

        while True:
            try:
                choice = int(input(f"\nВыберите файл (1-{len(drawio_files)}): "))
                if 1 <= choice <= len(drawio_files):
                    selected_file = drawio_files[choice - 1]
                    self.selected_file = selected_file
                    print(f"Выбран файл: {selected_file}")
                    return selected_file
                else:
                    print("Неверный номер файла. Пожалуйста, попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число.")
            except KeyboardInterrupt:
                print("\nОперация прервана пользователем.")
                return None

    def read_file_content(self, filename: str) -> Optional[str]:
        """
        Чтение содержимого файла drawio

        :param filename: имя файла для чтения
        :return: содержимое файла в виде строки или None в случае ошибки
        """
        filepath = os.path.join(self.data_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
        except FileNotFoundError:
            print(f"Файл {filepath} не найден.")
            return None
        except Exception as e:
            print(f"Ошибка при чтении файла {filepath}: {str(e)}")
            return None

    def parse_drawio_structure(self, filename: str) -> Optional[ET.Element]:
        """
        Разбор структуры файла drawio

        :param filename: имя файла для разбора
        :return: корневой элемент XML или None в случае ошибки
        """
        content = self.read_file_content(filename)

        if content is None:
            return None

        try:
            # Убираем возможные проблемы с XML, например, лишние символы в начале
            content = content.strip()

            # Парсим XML
            root = ET.fromstring(content)
            return root
        except ET.ParseError as e:
            print(f"Ошибка при разборе XML файла {filename}: {str(e)}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при разборе файла {filename}: {str(e)}")
            return None

    @staticmethod
    def load_stencil_templates(template_file: str = "stencil_templates.yaml"):
        """
        Загрузка шаблонов для поиска stencil объектов из YAML файла

        :param template_file: путь к файлу шаблонов (если не указан, используется stencil_templates.yaml в config)
        :return: словарь с шаблонами или None в случае ошибки
        """

        if not os.path.exists(template_file):
            print(f"Файл шаблонов {template_file} не найден.")
            return None

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
            return templates
        except Exception as e:
            print(f"Ошибка при загрузке шаблонов из {template_file}: {str(e)}")
            return None

    #######

    @staticmethod
    def _clean_html_content(text: str) -> str:
        """
        Удаляет HTML теги из строки и нормализует пробелы

        :param text: исходный текст, возможно содержащий HTML
        :return: очищенный текст
        """
        if '<' in text and '>' in text:  # Проверяем наличие HTML тегов
            clean_text = re.sub('<[^<]+?>', ' ', text).strip()
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Нормализуем пробелы
            clean_text = clean_text.replace('&nbsp;', ' ').strip()
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Еще раз нормализуем пробелы
            return clean_text
        return text

    def generate_summary_report(self, results_by_template: dict):
        """
        Генерация сводного отчета по найденным stencils

        :param results_by_template: словарь с результатами по каждому шаблону
        """
        print("\n" + "=" * 60)
        print("СВОДНЫЙ ОТЧЕТ ПО НАЙДЕННЫМ STENCILS")
        print("=" * 60)

        total_objects = 0
        for template_name, objects in results_by_template.items():
            if objects:
                print(f"\nШаблон: {template_name}")
                for obj in objects:
                    # Формируем строку с данными объекта
                    obj_str = f"  - ID: {obj['id']}"

                    if obj['extracted_data']:
                        # Выводим все данные из extracted_data в формате имя переменной : значение
                        for key, values in obj['extracted_data'].items():
                            for value in values:
                                # Проверяем, что значение не пустое
                                if value:
                                    # Очищаем значение от HTML тегов, если они есть
                                    clean_value = self._clean_html_content(str(value))
                                    # Проверяем, что после очистки значение не пустое
                                    if clean_value.strip():
                                        obj_str += f" {key}: {clean_value}"

                    print(obj_str)

                print(f"  Обнаружено объектов: {len(objects)}")
                total_objects += len(objects)
            else:
                print(f"\nШаблон: {template_name}")
                print(f"  Обнаружено объектов: 0")

        print("\n" + "=" * 60)
        print(f"ИТОГО: Обнаружено объектов {total_objects}")
        print("=" * 60)

    #####

    def find_stencils_by_all_templates(self, filename: str = None) -> dict:
        """
        Поиск stencils по всем шаблонам из файла шаблонов в указанном файле drawio

        :param filename: имя файла для поиска (если не указано, используется выбранный файл)
        :return: словарь с результатами по каждому шаблону
        """
        if filename is None:
            filename = self.selected_file

        if filename is None:
            print("Файл не выбран.")
            return {}

        # Загружаем шаблоны
        templates = self.load_stencil_templates()
        if not templates:
            print("Не удалось загрузить шаблоны.")
            return {}

        # Словарь для хранения результатов по каждому шаблону
        results_by_template = {}

        # Перебираем все шаблоны из файла и последовательно ищем их в исходном файле
        for template_name, template_config in templates.items():
            # Ищем объекты для текущего шаблона
            print(template_name)
            matched_objects = []

            # Читаем файл
            root = self.parse_drawio_structure(filename)
            if root is None:
                continue

            # Ищем все элементы mxCell
            for element in root.iter():
                if element.tag == 'mxCell':
                    # Создаем полную строку с содержимым элемента
                    element_string = self._get_full_element_string(element)

                    # Проверяем, соответствует ли элемент шаблону
                    matched = self._check_element_matches_patterns(element_string, template_config)

                    if matched:
                        # Извлекаем дополнительные данные с помощью парсеров
                        extracted_data = {}
                        parsed_values = {}  # Словарь для хранения всех найденных значений парсеров

                        if 'parsers' in template_config:
                            for parser_item in template_config['parsers']:
                                for data_name, regex_pattern in parser_item.items():
                                    matches = re.findall(regex_pattern, element.get('value', ''), re.IGNORECASE)
                                    if matches:
                                        extracted_data[data_name] = matches
                                        # Сохраняем все найденные значения для возможного использования в других операциях
                                        parsed_values[data_name] = matches

                        # Извлекаем информацию о найденном объекте
                        obj_info = {
                            'id': element.get('id', ''),
                            'value': element.get('value', ''),
                            'style': element.get('style', ''),
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

        return results_by_template

    def _get_full_element_string(self, element) -> str:
        """
        Создает полную строку с содержимым элемента

        :param element: XML элемент
        :return: строка с полным содержимым элемента
        """
        # Собираем все атрибуты элемента
        attrs = []
        for attr_name, attr_value in element.attrib.items():
            attrs.append(f'{attr_name}="{attr_value}"')

        # Добавляем значение элемента
        value = element.get('value', '')
        if value:
            attrs.append(f'value="{value}"')

        return ' '.join(attrs)

    def _check_element_matches_patterns(self, element_string: str, template_config: dict) -> bool:
        """
        Проверяет, соответствует ли элемент шаблону

        :param element_string: строковое представление элемента
        :param template_config: конфигурация шаблона
        :return: True если элемент соответствует шаблону
        """
        if 'patterns' not in template_config:
            return False

        for pattern in template_config['patterns']:
            if '|' in pattern or '!' in pattern:
                # Используем сложную логику для ИЛИ и НЕ
                if self._evaluate_complex_pattern(pattern, element_string):
                    return True
            else:
                # Простая логика И
                if self._evaluate_simple_pattern(pattern, element_string):
                    return True

        return False

    def _evaluate_simple_pattern(self, pattern: str, element_string: str) -> bool:
        """
        Проверяет простой паттерн (только И)

        :param pattern: паттерн для проверки
        :param element_string: строковое представление элемента
        :return: True если паттерн соответствует
        """
        # Разбиваем паттерн на отдельные критерии по разделителю ':'
        criteria = pattern.split(':')

        for criterion in criteria:
            criterion = criterion.strip().lower()
            if criterion and criterion not in element_string.lower():
                return False

        return True

    def _evaluate_complex_pattern(self, pattern: str, element_string: str) -> bool:
        """
        Оценка сложного паттерна с логическими операторами

        :param pattern: паттерн с логическими операторами
        :param element_string: строковое представление элемента
        :return: True если паттерн соответствует
        """
        search_text = element_string.lower()

        # Разбиваем паттерн по ИЛИ (|)
        or_parts = pattern.split('|')

        for or_part in or_parts:
            # Проверяем части на наличие НЕ (!)
            and_parts = []
            current_part = ""

            i = 0
            while i < len(or_part):
                if or_part[i] == '!':
                    # Сохраняем предыдущую часть
                    if current_part.strip():
                        and_parts.append(('AND', current_part.strip()))
                    current_part = ""

                    # Пропускаем ! и собираем следующую часть
                    i += 1
                    negated_part = ""
                    while i < len(or_part) and or_part[i] != ':':
                        negated_part += or_part[i]
                        i += 1
                    and_parts.append(('NOT', negated_part.strip()))
                elif or_part[i] == ':':
                    if current_part.strip():
                        and_parts.append(('AND', current_part.strip()))
                        current_part = ""
                    i += 1
                else:
                    current_part += or_part[i]
                    i += 1

            # Добавляем последнюю часть
            if current_part.strip():
                and_parts.append(('AND', current_part.strip()))

            # Проверяем условия И и НЕ
            or_part_match = True
            for op, part in and_parts:
                if op == 'AND':
                    if part and part.lower() not in search_text:
                        or_part_match = False
                        break
                elif op == 'NOT':
                    if part and part.lower() in search_text:
                        or_part_match = False
                        break

            if or_part_match:
                return True

        return False