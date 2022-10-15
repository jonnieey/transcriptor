class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def show_items(self, items):
        # items = list(self.model)
        item_type = self.model.item_type
        self.view.show_item_list(item_type, items)
