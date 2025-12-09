def replace_content(self, ws: Worksheet, infos: dict) -> None:

    nb_row, nb_col = ExcelManager.get_dimensions(ws)
    nb_changes = 0

    # instruction column
    has_column_instruction = self.get_text(ws, 1, 1) == "colonne_instruction"
    column_instruction = None
    first_column = 2 if has_column_instruction else 1
    if has_column_instruction:
        # read column instruction
        column_instruction = [self.get_text(ws, row, col=1) for row in range(1, nb_row)]
        # erase text column instruction
        for row in range(1, nb_row):
            ws.cell(row, 1, value="")

    # independent info

    # -- filter
    independent_infos = {
        info_name: value for info_name, value in infos.items() if isinstance(value, str)
    }

    print(independent_infos)

    # -- replace
    for row, col in itertools.product(range(1, n), range(1, n)):
        nb_changes += self.replace_text_in_cell(ws, row, col, independent_infos)

    print(f"Excel changes indenpendent : {nb_changes}")

    # list info

    if not column_instruction:
        return nb_changes

    # -- filter
    list_infos = {
        info_name: value
        for info_name, value in infos.items()
        if isinstance(value, list)
    }

    # -- read instructions
    lists_rows: Dict[str, Tuple[str, str]] = {}
    name_list = None
    for idx_row, text in enumerate(column_instruction):
        if text is None or not ":" in text:
            continue

        instruction, name_list_current = text.split(":")
        print(">", instruction, name_list_current)
        if name_list != name_list_current:
            assert instruction == "debut_liste"
            name_list = name_list_current
            lists_rows[name_list] = (idx_row + 1, None)
        else:
            assert instruction == "fin_liste"
            lists_rows[name_list] = (lists_rows[name_list][0], idx_row + 1)

    print(lists_rows)

    # -- replace
    for list_name in lists_rows.keys():

        start_row, end_row = lists_rows[list_name]

        infos = list_infos.get(list_name)
        print("list_name :", list_name, ";", "infos :", infos)
        if infos is None:
            continue

        # insert rows
        nb_rows_list = end_row - start_row + 1
        nb_to_add = nb_rows_list * (len(infos) - 1)
        ws.insert_rows(end_row + 1, amount=nb_to_add)
        print("nb_to_add :", nb_to_add)

        # copy content
        texts: List[List[str]] = [
            [ws.cell(row, col).value for col in range(first_column, 10)]
            for row in range(start_row, end_row + 1)
        ]

        for idx in range(1, len(infos)):
            for offset_row, lst in enumerate(texts):
                row = start_row + nb_rows_list * idx + offset_row

                for col, cell_value in enumerate(lst, start=first_column):
                    cell_value_copy = (
                        cell_value
                        if not isinstance(cell_value, CellRichText)
                        else CellRichText(cell_value.copy())
                    )
                    if cell_value_copy:
                        print(cell_value, cell_value_copy)
                        ws.cell(row, col, value=cell_value_copy)

        # update other start and end
        for list_name_c in lists_rows.keys():
            start_row_c, end_row_c = lists_rows[list_name_c]
            lists_rows[list_name_c] = start_row_c + nb_to_add, end_row_c + nb_to_add

        # fill row
        for idx_element, infos_one_element in enumerate(infos):
            infos_one_element = {
                f"{list_name}:{sub_name}": value
                for sub_name, value in infos_one_element.items()
            }
            print("infos_one_element :", infos_one_element)

            offset = idx_element * nb_rows_list
            for row, col in itertools.product(
                range(start_row + offset, end_row + offset + 1),
                range(first_column, n),
            ):
                nb_changes += self.replace_text_in_cell(ws, row, col, infos_one_element)

    print(f"Excel changes list : {nb_changes}")
