import customtkinter as ctk

def move_cursor_left(event):
    # Перемещение курсора в начало предыдущего слова
    index = event.widget.index(ctk.INSERT)
    new_index = event.widget.search(r'\m\w+', index, stopindex="1.0", backwards=True, regexp=True)
    if new_index:
        event.widget.mark_set(ctk.INSERT, new_index)
    return "break"

def move_cursor_right(event):
    # Перемещение курсора в конец следующего слова
    index = event.widget.index(ctk.INSERT)
    new_index = event.widget.search(r'\m\w+', index, stopindex=ctk.END, regexp=True)
    if new_index:
        event.widget.mark_set(ctk.INSERT, f"{new_index} wordend")
    return "break"

def select_word_left(event):
    # Выделение текста от курсора до начала предыдущего слова
    index = event.widget.index(ctk.INSERT)
    new_index = event.widget.search(r'\m\w+', index, stopindex="1.0", backwards=True, regexp=True)
    if new_index:
        event.widget.tag_add(ctk.SEL, new_index, ctk.INSERT)
        event.widget.mark_set(ctk.INSERT, new_index)
    return "break"

def select_word_right(event):
    # Выделение текста от курсора до конца следующего слова
    index = event.widget.index(ctk.INSERT)
    new_index = event.widget.search(r'\m\w+', index, stopindex=ctk.END, regexp=True)
    if new_index:
        event.widget.tag_add(ctk.SEL, ctk.INSERT, f"{new_index} wordend")
        event.widget.mark_set(ctk.INSERT, f"{new_index} wordend")
    return "break"