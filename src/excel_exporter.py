import logging
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

class ExcelExporter:
    @staticmethod
    def export_to_excel(parent, company_table):
        try:
            filename, _ = QFileDialog.getSaveFileName(parent, "Export Excel", "", "Excel Files (*.xlsx)")
            if not filename:
                return

            if not filename.endswith('.xlsx'):
                filename += '.xlsx'

            headers = [
                "Telephely név", "Telephely kód", "Összes terminál igény", "Kiadva", "Kihelyezés",
                "Áram", "Elosztó", "Szoftver", "Teszt", "Véglegesítve", "Megjegyzés",
                "Megjegyzés ideje", "Véglegesités ideje"
            ]

            wb = Workbook()
            ws = wb.active

            # Add headers with formatting
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Add data
            for row in range(company_table.rowCount()):
                row_data = []
                for col in range(1, company_table.columnCount()):  # Start from 1 to skip 'Select' column
                    item = company_table.item(row, col)
                    value = item.text() if item else ""
                    if value.lower() in ['true', 'false', 'van', 'nincs']:
                        value = "Van" if value.lower() in ['true', 'van'] else "Nincs"
                    row_data.append(value)

                # Map the data to the correct columns
                mapped_data = [
                    row_data[1] if len(row_data) > 1 else "",  # Telephely név (CompanyName)
                    row_data[0] if len(row_data) > 0 else "",  # Telephely kód (ID)
                    "",  # Összes terminál igény (not available)
                    "Van" if row_data[4] == "KIADVA" else "Nincs" if len(row_data) > 4 else "",  # Kiadva
                    row_data[4] if len(row_data) > 4 else "",  # Kihelyezés (Telepítés)
                    row_data[5] if len(row_data) > 5 else "",  # Áram
                    row_data[6] if len(row_data) > 6 else "",  # Elosztó
                    row_data[8] if len(row_data) > 8 else "",  # Szoftver
                    "Van" if row_data[4] == "HELYSZINEN_TESZTELVE" else "Nincs" if len(row_data) > 4 else "",  # Teszt
                    "Van" if row_data[4] == "KIRAKVA" else "Nincs" if len(row_data) > 4 else "",  # Véglegesítve
                    "",  # Megjegyzés (not available)
                    "",  # Megjegyzés ideje (not available)
                    row_data[-1] if row_data else ""  # Véglegesités ideje (LastModified)
                ]

                ws.append(mapped_data)

            wb.save(filename)

            QMessageBox.information(parent, "Export Complete", f"Data exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            QMessageBox.critical(parent, "Error", f"Failed to export to Excel: {str(e)}")