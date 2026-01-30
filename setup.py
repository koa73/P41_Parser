from setuptools import setup, find_packages

setup(
    name="P41_DrawIO_Parser",
    version="1.0.0",
    description="Модульный проект для обработки файлов DrawIO",
    author="Oleg",
    packages=find_packages(),
    install_requires=[
        # Зависимостей нет, так как используем стандартные библиотеки
    ],
    entry_points={
        'console_scripts': [
            'drawio-parser = main:main',
        ],
    },
)