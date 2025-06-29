import os
from datetime import datetime
from typing import List, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


async def generate_invoice_excel(
    invoice_data: List[Tuple],
    invoice_number: str = None,
    output_dir: str = "invoices"
) -> str:
    """
    Генерирует накладную в Excel формате из переданных данных.
    
    Args:
        invoice_data: Список кортежей с данными товаров
        invoice_number: Номер накладной (если не указан, генерируется автоматически)
        output_dir: Директория для сохранения файла
        
    Returns:
        Путь к созданному Excel файлу
    """
    # Создаем директорию если не существует
    os.makedirs(output_dir, exist_ok=True)
    
    # Генерируем номер накладной если не указан
    if not invoice_number:
        invoice_number = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Создаем новый workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Накладная"
    
    # Настройка стилей
    header_font = Font(name='Arial', size=16, bold=True)
    title_font = Font(name='Arial', size=12, bold=True)
    normal_font = Font(name='Arial', size=10)
    bold_font = Font(name='Arial', size=10, bold=True)
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    right_alignment = Alignment(horizontal='right', vertical='center')
    
    # Заголовок накладной
    ws.merge_cells('A1:I2')
    ws['A1'] = f'ТОВАРНАЯ НАКЛАДНАЯ № {invoice_number}'
    ws['A1'].font = header_font
    ws['A1'].alignment = center_alignment
    
    # Дата накладной
    ws.merge_cells('A3:I3')
    ws['A3'] = f'от {datetime.now().strftime("%d.%m.%Y")}'
    ws['A3'].font = normal_font
    ws['A3'].alignment = center_alignment
    
    # Информация о компании (из первой записи)
    if invoice_data:
        company_name = invoice_data[0][0]
        ws.merge_cells('A5:D5')
        ws['A5'] = f'Поставщик: {company_name}'
        ws['A5'].font = bold_font
        ws['A5'].alignment = left_alignment
    
    # Заголовки таблицы
    headers = ['№', 'Код товара', 'Наименование', 'Количество', 'Ед.изм.', 
               'Цена', 'Сумма', 'Статус', 'Дата']
    
    start_row = 7
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=col, value=header)
        cell.font = title_font
        cell.alignment = center_alignment
        cell.border = thin_border
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    # Заполнение данными
    total_sum = 0
    current_row = start_row + 1
    
    for idx, item in enumerate(invoice_data, 1):
        # Распаковка данных
        company, code, name, date, operation, quantity, price, amount, status = item
        
        # Заполнение строки
        ws.cell(row=current_row, column=1, value=idx).alignment = center_alignment
        ws.cell(row=current_row, column=2, value=code).alignment = center_alignment
        ws.cell(row=current_row, column=3, value=name).alignment = left_alignment
        ws.cell(row=current_row, column=4, value=quantity).alignment = center_alignment
        ws.cell(row=current_row, column=5, value='шт.').alignment = center_alignment
        ws.cell(row=current_row, column=6, value=f"{price:,.2f}").alignment = right_alignment
        ws.cell(row=current_row, column=7, value=f"{amount:,.2f}").alignment = right_alignment
        ws.cell(row=current_row, column=8, value=status).alignment = center_alignment
        ws.cell(row=current_row, column=9, value=date.strftime("%d.%m.%Y %H:%M")).alignment = center_alignment
        
        # Применение границ
        for col in range(1, 10):
            ws.cell(row=current_row, column=col).border = thin_border
            ws.cell(row=current_row, column=col).font = normal_font
        
        total_sum += amount
        current_row += 1
    
    # Итоговая строка
    ws.merge_cells(f'A{current_row}:F{current_row}')
    ws[f'A{current_row}'] = 'ИТОГО:'
    ws[f'A{current_row}'].font = bold_font
    ws[f'A{current_row}'].alignment = right_alignment
    ws[f'A{current_row}'].border = thin_border
    
    ws[f'G{current_row}'] = f"{total_sum:,.2f}"
    ws[f'G{current_row}'].font = bold_font
    ws[f'G{current_row}'].alignment = right_alignment
    ws[f'G{current_row}'].border = thin_border
    
    # Подписи
    current_row += 3
    ws[f'A{current_row}'] = 'Отпустил: ________________'
    ws[f'F{current_row}'] = 'Получил: ________________'
    
    current_row += 2
    ws[f'A{current_row}'] = 'М.П.'
    ws[f'F{current_row}'] = 'М.П.'
    
    # Настройка ширины колонок
    column_widths = [5, 12, 40, 12, 8, 15, 15, 20, 18]
    for idx, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    
    # Сохранение файла
    filename = f"invoice_{invoice_number}.xlsx"
    filepath = os.path.join(output_dir, filename)
    wb.save(filepath)
    
    return filepath


# Пример использования
if __name__ == "__main__":
    # Тестовые данные
    test_data = [
        ('AVTOLIDER', 11113, 'Подфарник боковой', datetime(2024, 12, 10, 22, 10, 21), 
         'Продажа', 12.0, 35000.0, 420000.0, 'Ожидает оплаты'),
        ('AVTOLIDER', 10611, 'Лист рессорная задняя  25*90  Nº2  173см—Д', 
         datetime(2024, 12, 10, 22, 10, 21), 'Продажа', 1.0, 500000.0, 500000.0, 'Ожидает оплаты'),
        ('AVTOLIDER', 10939, 'Втулка торсиона кабины HOWO фторопласт LEO', 
         datetime(2024, 12, 10, 22, 10, 21), 'Продажа', 2.0, 30000.0, 60000.0, 'Ожидает оплаты')
    ]
    
    # Генерация накладной
    invoice_path = generate_invoice_excel(test_data)
    print(f"Накладная создана: {invoice_path}")
