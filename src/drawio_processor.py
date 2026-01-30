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

    def process_selected_file(self):
        """
        Обработка выбранного файла
        """
        if self.selected_file is None:
            print("Файл не выбран.")
            return

        print(f"Чтение содержимого файла: {self.selected_file}")
        content = self.read_file_content(self.selected_file)

        if content is not None:
            print(f"Файл успешно прочитан. Размер: {len(content)} символов")
            print("-" * 50)
            # Выводим первые 500 символов для демонстрации
            print(content[:500])
            if len(content) > 500:
                print("...")
            print("-" * 50)
        else:
            print("Не удалось прочитать файл.")

    @staticmethod
    def load_stencil_templates(template_file: str = None):
        """
        Загрузка шаблонов для поиска stencil объектов из YAML файла

        :param template_file: путь к файлу шаблонов (если не указан, используется stencil_templates.yaml в config)
        :return: словарь с шаблонами или None в случае ошибки
        """
        if template_file is None:
            template_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "stencil_templates.yaml")

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

    def find_stencils_by_all_templates_(self, filename: str = None) -> dict:
        """
        Поиск стencилов по всем шаблонам из файла шаблонов в указанном файле drawio

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
            matched_objects = []

            # Читаем файл
            root = self.parse_drawio_structure(filename)
            if root is None:
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
                                desc_text = re.sub('<[^<]+?>', ' ', desc_text).strip()
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

        return results_by_template

    def generate_summary_report(self, results_by_template: dict):
        """
        Генерация сводного отчета по найденным стencилам

        :param results_by_template: словарь с результатами по каждому шаблону
        """
        print("\n" + "="*60)
        print("СВОДНЫЙ ОТЧЕТ ПО НАЙДЕННЫМ STENCILS")
        print("="*60)

        total_objects = 0
        for template_name, objects in results_by_template.items():
            if objects:
                print(f"\nШаблон: {template_name}")
                for obj in objects:
                    # Формируем строку с данными объекта
                    obj_str = f"  - ID: {obj['id']}"
                    if obj['extracted_data']:
                        # Добавляем IP-адреса, если они есть
                        if 'ip' in obj['extracted_data']:
                            ip_list = obj['extracted_data']['ip']
                            for ip in ip_list:
                                obj_str += f" ip:{ip}"

                        # Добавляем описание, если оно есть
                        if 'description' in obj['extracted_data']:
                            desc_list = obj['extracted_data']['description']
                            for desc in desc_list:
                                # Очищаем описание от HTML тегов и лишних пробелов
                                clean_desc = re.sub('<[^<]+?>', '', desc).strip()
                                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()  # Нормализуем пробелы
                                if clean_desc:  # Выводим только если описание не пустое
                                    obj_str += f" Description: {clean_desc}"

                    print(obj_str)

                print(f"  Обнаружено объектов: {len(objects)}")
                total_objects += len(objects)
            else:
                print(f"\nШаблон: {template_name}")
                print(f"  Обнаружено объектов: 0")

        print("\n" + "="*60)
        print(f"ИТОГО: Обнаружено объектов {total_objects}")
        print("="*60)

    def find_stencils_by_all_templates(self, filename: str = None) -> dict:
        """
        Поиск стencилов по всем шаблонам из файла шаблонов в указанном файле drawio

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
            matched_objects = []

            # Читаем файл
            root = self.parse_drawio_structure(filename)
            if root is None:
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
                            parsed_values = {}  # Словарь для хранения всех найденных значений парсеров

                            if 'parsers' in template_config:
                                for parser_item in template_config['parsers']:
                                    for data_name, regex_pattern in parser_item.items():
                                        matches = re.findall(regex_pattern, value, re.IGNORECASE)
                                        if matches:
                                            extracted_data[data_name] = matches
                                            # Сохраняем все найденные значения для возможного использования в других операциях
                                            parsed_values[data_name] = matches

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

        return results_by_template
