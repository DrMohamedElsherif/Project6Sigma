import sys
import subprocess
import os
import math

# 1. Ensure xlsxwriter is installed
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])
    import xlsxwriter


def estimate_row_height(text, col_width, base_height=32):
    """
    Estimate Excel row height based on text length and column width.
    This is a heuristic because xlsxwriter cannot auto-size rows.
    """
    if not text:
        return base_height

    approx_chars_per_line = col_width * 1.1
    lines = math.ceil(len(str(text)) / approx_chars_per_line)
    return base_height + (lines - 1) * 18


def create_advanced_timesheet(output_path, initial_year, user_name, role, hourly_wage, max_hours):
    workbook = xlsxwriter.Workbook(output_path)

    # --- STYLES ---
    base_label = {
        'bold': True, 'bg_color': '#F8F9FA', 'border': 1, 'border_color': '#DDE1E6',
        'font_name': 'Segoe UI', 'font_size': 14, 'valign': 'vcenter', 'indent': 1
    }
    base_value = {
        'bg_color': '#FFFFFF', 'border': 1, 'border_color': '#DDE1E6', 'align': 'center',
        'valign': 'vcenter', 'font_name': 'Segoe UI', 'font_size': 14, 'font_color': '#343A40'
    }

    # MONTHLY HEADER STYLES (UPDATED: text_wrap enabled)
    header_label_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white',
        'top': 1, 'bottom': 1, 'left': 1, 'border_color': '#102A43',
        'valign': 'vcenter', 'font_name': 'Segoe UI', 'indent': 1,
        'text_wrap': True
    })

    header_val_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#FFFFFF', 'font_color': '#1F4E78',
        'top': 1, 'bottom': 1, 'right': 1, 'border_color': '#102A43',
        'valign': 'vcenter', 'align': 'center', 'font_name': 'Segoe UI',
        'text_wrap': True
    })

    column_label_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'border_color': '#92A8D1',
        'align': 'center', 'valign': 'vcenter', 'font_name': 'Segoe UI', 'font_size': 11
    })

    date_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1, 'font_name': 'Segoe UI'})
    time_fmt = workbook.add_format({'num_format': '[hh]:mm:ss', 'border': 1, 'font_name': 'Segoe UI'})
    curr_fmt = workbook.add_format({'num_format': '#,##0.00" €"', 'border': 1, 'font_name': 'Segoe UI'})
    std_fmt = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Segoe UI', 'valign': 'vcenter'})

    time_sum_style = workbook.add_format({
        'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
        'num_format': '[hh]:mm:ss', 'align': 'center', 'valign': 'vcenter'
    })
    curr_sum_style = workbook.add_format({
        'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
        'num_format': '#,##0.00" €"', 'align': 'center', 'valign': 'vcenter'
    })
    label_sum_style = workbook.add_format({
        'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
        'align': 'right', 'valign': 'vcenter'
    })

    # --- SHEET 1: YEAR CONFIG (PRETTY & PROFESSIONAL DASHBOARD) ---
    cfg = "Year_Config"
    config_sheet = workbook.add_worksheet(cfg)
    config_sheet.hide_gridlines(2)
    config_sheet.set_tab_color('#2F5597')

    # Layout - WIDER COLUMNS to prevent truncation
    config_sheet.set_column('A:A', 4)
    config_sheet.set_column('B:B', 42)  # WIDER for labels to prevent truncation
    config_sheet.set_column('C:C', 37)  # WIDER for values to prevent wrapping

    # --- Title ---
    title_fmt = workbook.add_format({
        'bold': True,
        'font_size': 22,
        'font_name': 'Segoe UI',
        'font_color': '#1F4E78',
        'align': 'left',
        'valign': 'vcenter'
    })

    subtitle_fmt = workbook.add_format({
        'font_size': 11,
        'font_name': 'Segoe UI',
        'font_color': '#6C757D'
    })

    # FIX 1: Wider merged range for title to prevent "Konfiguration" truncation
    config_sheet.merge_range('B7:C7', '⏱️  Arbeitszeitnachweis - Konfiguration', title_fmt)
    config_sheet.merge_range('B8:C8', 'Jahreseinstellungen & Mitarbeiterprofil', subtitle_fmt)

    # --- Logo (unchanged behavior) ---
    logo_path = os.path.join(os.path.dirname(output_path), 'l2s.png')
    if os.path.exists(logo_path):
        config_sheet.insert_image(
            'B1',
            logo_path,
            {'x_offset': 0, 'y_offset': 8, 'x_scale': 1.25, 'y_scale': 1.25}
        )

    # --- ENHANCED CARD STYLES FOR BETTER VISUAL APPEAL ---
    
    # Different background colors for each row with matching icons
    row_colors = [
        {'bg': '#E3F2FD', 'icon': '📅', 'border': '#90CAF9'},  # Calendar - light blue
        {'bg': '#F3E5F5', 'icon': '👤', 'border': '#CE93D8'},  # User - light purple
        {'bg': '#E8F5E8', 'icon': '🎯', 'border': '#A5D6A7'},  # Role - light green
        {'bg': '#FFF3E0', 'icon': '💶', 'border': '#FFCC80'},  # Wage - light orange
        {'bg': '#F1F8E9', 'icon': '⏰', 'border': '#C5E1A5'},  # Hours - light lime
    ]

    dashboard_data = [
        ('Kalenderjahr', initial_year),
        ('Vorname, Name', user_name),
        ('Berufliche Funktion', role),
        ('Stundensatz (€)', hourly_wage),
        ('Maximale Wochenstunden', max_hours),
    ]

    start_row = 9

    for i, (label, value) in enumerate(dashboard_data):
        r = start_row + i
        config_sheet.set_row(r, 50)  # Taller rows for better appearance
        
        row_color = row_colors[i]
        
        # Create UNIQUE format for EACH row (for visual variety)
        label_fmt = workbook.add_format({
            'bold': True,
            'font_name': 'Segoe UI',
            'font_size': 12,  # Slightly larger font
            'font_color': '#2C3E50',
            'bg_color': row_color['bg'],
            'align': 'left',
            'valign': 'vcenter',
            'indent': 2,
            'top': 2,
            'bottom': 2,
            'left': 4,
            'right': 0,
            'border': 1,
            'border_color': row_color['border'],
            'locked': True,  # LABELS ARE LOCKED
            'text_wrap': True  # Wrap text if needed
        })
        
        # Add icon to label
        icon_label = f"{row_color['icon']}  {label}"
        
        value_fmt = workbook.add_format({
            'bold': True,
            'font_name': 'Segoe UI',
            'font_size': 13,  # Slightly larger for values
            'font_color': '#1A237E',  # Darker blue for values
            'bg_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'top': 2,
            'bottom': 2,
            'left': 0,
            'right': 4,
            'border': 1,
            'border_color': row_color['border'],
            'locked': False,  # VALUES ARE UNLOCKED (EDITABLE)
            'text_wrap': True
        })
        
        # Special formatting for numeric values
        if i == 0:  # Year
            value_fmt.set_num_format('0')
            value_fmt.set_font_color('#0D47A1')
        elif i == 3:  # Hourly wage
            value_fmt.set_num_format('#,##0.00" €"')
            value_fmt.set_font_color('#1B5E20')
            value_fmt.set_bold(True)
        elif i == 4:  # Max hours
            value_fmt.set_num_format('0" h"')
            value_fmt.set_font_color('#BF360C')
            value_fmt.set_bold(True)
        
        # FIX 2: Adjust formatting for role (Lean Six Sigma Working Student)
        if i == 2:  # Role
            #value_fmt.set_font_size(12)  # Slightly smaller to fit in one line
            value_fmt.set_text_wrap(True)  # Allow wrapping if absolutely necessary
            value_fmt.set_align('center')
            value_fmt.set_valign('vcenter')
        
        # Special styling for user name (make it stand out)
        if i == 1:
            value_fmt.set_font_color('#4A148C')
            #value_fmt.set_font_size(14)
            value_fmt.set_bg_color('#F5F5F5')
        
        # Write the data
        config_sheet.write(r, 1, icon_label, label_fmt)
        config_sheet.write(r, 2, value, value_fmt)

        # Add subtle shadow effect by setting adjacent cell colors
        config_sheet.write_blank(r, 0, workbook.add_format({'bg_color': row_color['bg']}))

    # --- ADD SEPARATOR LINE AFTER TABLE ---
    separator_row = start_row + len(dashboard_data)
    config_sheet.set_row(separator_row, 8)  # Smaller separator row
    config_sheet.merge_range(f'B{separator_row+1}:C{separator_row+1}', '', 
                            workbook.add_format({'top': 2, 'border_color': '#B0BEC5'}))

    # --- ADD INFO TEXT BELOW TABLE ---
    info_row = separator_row + 2
    # FIX 3: Smaller row height for info text to reduce empty space
    config_sheet.set_row(info_row, 30)  # Reduced from 60 to 40
    
    info_fmt = workbook.add_format({
        'font_name': 'Segoe UI',
        'font_size': 10,
        'font_color': '#546E7A',
        'italic': True,
        'text_wrap': True,
        'valign': 'top',  # Align to top to reduce space below
        'align': 'left',
        'bg_color': '#FAFAFA',
        'border': 1,
        'border_color': '#E0E0E0'
    })
    
    info_text = "ℹ️  Hinweis: Ändern Sie die Werte in der rechten Spalte (weiße Felder). " \
                "Diese Einstellungen werden automatisch auf alle Monatsblätter übertragen."
    
    config_sheet.merge_range(f'B{info_row+1}:C{info_row+1}', info_text, info_fmt)

    # --- PROTECT YEAR CONFIG SHEET (ALLOW EDITING IN COLUMN C ONLY) ---
    config_sheet.protect(
        password='l2s123',  # Change this password as needed
        options={
            'objects': True,                # Allow graphic objects
            'scenarios': True,              # Allow scenarios
            'format_cells': False,          # Disallow cell formatting
            'format_columns': False,        # Disallow column formatting
            'format_rows': False,           # Disallow row formatting
            'insert_columns': False,        # Disallow inserting columns
            'insert_rows': False,           # Disallow inserting rows
            'insert_hyperlinks': False,     # Disallow inserting hyperlinks
            'delete_columns': False,        # Disallow deleting columns
            'delete_rows': False,           # Disallow deleting rows
            'select_locked_cells': True,    # Allow selecting locked cells (viewing)
            'select_unlocked_cells': True,  # Allow selecting unlocked cells
            'sort': False,                  # Disallow sorting
            'autofilter': False,            # Disallow autofilter
            'pivot_tables': False,          # Disallow pivot tables
            'sheet': True                   # Protect sheet
        }
    )

    # --- MONTHLY SHEETS ---
    months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]

    for month_idx, month_name in enumerate(months, start=1):
        sheet = workbook.add_worksheet(month_name)
        sheet.hide_gridlines(2) 
        # 🔥 FORCE RECALCULATION ON FIRST OPEN (REQUIRED)
        sheet.write_formula('Z1', '=NOW()')
        sheet.set_column('Z:Z', None, None, {'hidden': True})

        sheet.set_column('A:J', 14)
        sheet.set_column('F:F', 25)

        # === RESPONSIVE HEADER ROW HEIGHT ===
        longest_text = max(
            len(month_name),
            len(user_name),
            len(str(hourly_wage)),
            len(str(initial_year)),
            len(str(max_hours))
        )
        header_height = estimate_row_height(longest_text, 14)
        sheet.set_row(0, header_height)

        sheet.set_row(1, 25)

        # --- TOP HEADER ROW ---
        sheet.write('A1', "Monat:", header_label_fmt)
        sheet.write('B1', month_name, header_val_fmt)

        # FIX 4: Update formulas to force immediate calculation
        sheet.write('C1', "Name:", header_label_fmt)
        sheet.write_formula('D1', f"=IF('{cfg}'!$C$11=\"\",\"\",'{cfg}'!$C$11)", header_val_fmt)

        sheet.write('E1', "Std.-Lohn:", header_label_fmt)
        sheet.write_formula('F1', f"=IF('{cfg}'!$C$13=\"\",\"\",'{cfg}'!$C$13)", header_val_fmt)

        sheet.write('G1', "Jahr:", header_label_fmt)
        sheet.write_formula('H1', f"=IF('{cfg}'!$C$10=\"\",\"\",'{cfg}'!$C$10)", header_val_fmt)

        sheet.write('I1', "Max Std:", header_label_fmt)
        sheet.write_formula('J1', f"=IF('{cfg}'!$C$14=\"\",\"\",'{cfg}'!$C$14)", header_val_fmt)

        headers = ['Datum', 'Tag', 'Anfang', 'Ende', 'Pausen', 'Projekt',
                   'Arbeitszeit', 'Lohn', 'Wochen-Std', 'Wochen-Lohn']

        for col, text in enumerate(headers):
            sheet.write(1, col, text, column_label_fmt)

        # --- UNLOCK ONLY USER-INPUT CELLS (C3:F33) ---
        # Create unlocked format for user-input cells
        unlocked_time_fmt = workbook.add_format({
            'num_format': '[hh]:mm:ss',
            'border': 1,
            'font_name': 'Segoe UI',
            'locked': False  # THIS IS KEY: unlocks the cell
        })
        
        unlocked_std_fmt = workbook.add_format({
            'border': 1,
            'align': 'center',
            'font_name': 'Segoe UI',
            'valign': 'vcenter',
            'locked': False  # THIS IS KEY: unlocks the cell
        })

        for day in range(1, 32):
            row = day + 1
            ex_r = row + 1
            
            # FIX 5: Update date formula to force immediate calculation
            sheet.write_formula(row, 0, f'=IF(ISBLANK(\'{cfg}\'!$C$10),"",DATE(\'{cfg}\'!$C$10,{month_idx},{day}))', date_fmt)
            sheet.write_formula(row, 1, f'=IF(A{ex_r}="","",TEXT(A{ex_r}, "dddd"))', std_fmt)
            
            # UNLOCKED: User input cells (C, D, E, F)
            sheet.write(row, 2, "", unlocked_time_fmt)      # Anfang
            sheet.write(row, 3, "", unlocked_time_fmt)      # Ende
            sheet.write(row, 4, "", unlocked_time_fmt)      # Pausen
            sheet.write(row, 5, "", unlocked_std_fmt)       # Projekt
            
            # --- Add guiding messages using data validation ---
            sheet.data_validation(row, 2, row, 2, {
                'validate': 'text_length',
                'criteria': '>=0',
                'input_message': 'Enter start time (e.g., 8:00)'
            })
            sheet.data_validation(row, 3, row, 3, {
                'validate': 'text_length',
                'criteria': '>=0',
                'input_message': 'Enter end time (e.g., 17:00)'
            })
            sheet.data_validation(row, 4, row, 4, {
                'validate': 'text_length',
                'criteria': '>=0',
                'input_message': 'Enter break duration (e.g., 0:30)'
            })
            sheet.data_validation(row, 5, row, 5, {
                'validate': 'text_length',
                'criteria': '>=0',
                'input_message': 'Enter project name or code'
            })
            
            
            # Locked calculated cells
            sheet.write_formula(row, 6, f'=IF(OR(A{ex_r}="", C{ex_r}="", D{ex_r}=""), "", (D{ex_r}-C{ex_r}-IF(E{ex_r}="",0,E{ex_r})))', time_fmt)
            sheet.write_formula(row, 7, f'=IF(G{ex_r}="", "", G{ex_r}*24*$F$1)', curr_fmt)
            sheet.write_formula(row, 8, f'=IF(OR(A{ex_r+1}="", WEEKDAY(A{ex_r}, 2)=7), SUM(G$3:G{ex_r})-SUM(I$2:I{row}), "")', time_sum_style)
            sheet.write_formula(row, 9, f'=IF(I{ex_r}="", "", SUM(H$3:H{ex_r})-SUM(J$2:J{row}))', curr_sum_style)

        sheet.write(34, 5, "Monatssumme: ", label_sum_style)
        sheet.write_formula(34, 6, "=SUM(G3:G33)", time_sum_style)
        sheet.write_formula(34, 7, "=SUM(H3:H33)", curr_sum_style)

        weekend_fmt = workbook.add_format({'bg_color': '#FFEFB1', 'border': 1})
        sheet.conditional_format(
            'A3:J33',
            {'type': 'formula', 'criteria': '=AND($A3<>"", WEEKDAY($A3, 2)>5)', 'format': weekend_fmt}
        )

        # --- PROTECT MONTHLY SHEETS (ALLOW EDITING ONLY IN C3:F33) ---
        sheet.protect(
            password='l2s123',  # Change this password as needed
            options={
                'objects': False,               # Allow graphic objects
                'scenarios': False,             # Allow scenarios
                'format_cells': False,          # Disallow cell formatting
                'format_columns': False,        # Disallow column formatting
                'format_rows': False,           # Disallow row formatting
                'insert_columns': False,        # Disallow inserting columns
                'insert_rows': False,           # Disallow inserting rows
                'insert_hyperlinks': False,     # Disallow inserting hyperlinks
                'delete_columns': False,        # Disallow deleting columns
                'delete_rows': False,           # Disallow deleting rows
                'select_locked_cells': True,    # Allow selecting locked cells (viewing)
                'select_unlocked_cells': True,  # Allow selecting unlocked cells
                'sort': False,                  # Disallow sorting
                'autofilter': False,            # Disallow autofilter
                'pivot_tables': False,          # Disallow pivot tables
                'sheet': True                   # Protect sheet
            }
        )
        
    # ✅ THIS IS THE REAL FIX
    #workbook.set_calc_mode('auto')
    #workbook.calc_on_load = True


    workbook.close()
    print(f"✅ Erfolg! Professionelle Stundenzettel erstellt unter: {output_path}")
    print("🔒 Passwort für alle Blätter: l2s123")
    print("\n🔧 KORREKTUREN:")
    print("  • Breitere Spalten (B:42, C:35) für bessere Lesbarkeit")
    print("  • 'Konfiguration' wird nicht mehr abgeschnitten")
    print("  • 'Lean Six Sigma Working Student' passt besser in eine Zeile")
    print("  • Info-Text mit weniger Leerraum darunter")
    print("\n⚡ FORMULA FIXES FOR IMMEDIATE CALCULATION:")
    print("  • Added volatile NOW() function to force Excel calculation")
    print("  • Updated header formulas with IF() checks")
    print("  • Updated date formulas with ISBLANK() checks")
    print("\n🎨 VISUELLE VERBESSERUNGEN:")
    print("  • Farbige Reihen mit unterschiedlichen Hintergründen")
    print("  • Passende Icons für jede Kategorie")
    print("  • Hervorgehobene Werte mit spezieller Formatierung")
    print("  • Informationsfeld mit Hinweisen")
    print("  • Verbesserte Abstände und Lesbarkeit")


create_advanced_timesheet(
    output_path='/home/l2s-team/Downloads/L2S_Header_Refined.xlsx',
    initial_year=2025,
    user_name='Mohamed Elsherif',
    role='Lean Six Sigma Working Student',
    hourly_wage=15.00,
    max_hours=20
)